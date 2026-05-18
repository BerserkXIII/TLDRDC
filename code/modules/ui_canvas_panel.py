import tkinter as tk

from .ui_config import COLORES, CANVAS_LAYER_TAGS, CANVAS_LAYER_ORDER
from .ui_imagen_manager import imagen_manager


class CanvasPanel:
    """
    Canvas-first rendering surface for one UI panel.

    The class keeps a stable set of layer tags:
    background -> content -> fx. Current widget panels can keep using their
    legacy frame while new renderers draw directly on this canvas.
    """

    def __init__(
        self,
        parent,
        ruta_fondo=None,
        color_fondo=COLORES["fondo_panel"],
        padding=0,
        resize_delay_ms=16,
    ):
        self.parent = parent
        self.color_fondo = color_fondo
        self.layer_tags = CANVAS_LAYER_TAGS
        self.padding = self._normalizar_padding(padding)
        self.resize_delay_ms = resize_delay_ms

        self.canvas = tk.Canvas(
            parent,
            bg=color_fondo,
            highlightthickness=0,
            relief="flat",
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._ruta_fondo = None
        self._background_item = None
        self._background_image = None
        self._image_refs = {}
        self._item_layers = {}
        self._resize_after_id = None
        self._resize_callbacks = []
        self._last_size = (0, 0)

        self.canvas.bind("<Configure>", self._programar_redibujado)
        self.set_background(ruta_fondo)

    @property
    def widget(self):
        """Tk widget owned by this panel."""
        return self.canvas

    def size(self):
        """Return current canvas size as (width, height)."""
        return (self.canvas.winfo_width(), self.canvas.winfo_height())

    def content_bounds(self):
        """Return drawable content box after padding: (x, y, width, height)."""
        width, height = self.size()
        left, top, right, bottom = self.padding
        return (
            left,
            top,
            max(width - left - right, 1),
            max(height - top - bottom, 1),
        )

    def add_resize_callback(self, callback):
        """Register a callback(canvas_panel) fired after resize debounce."""
        self._resize_callbacks.append(callback)

    def set_background(self, ruta_fondo):
        """Set or clear the background image path."""
        self._ruta_fondo = ruta_fondo
        if not ruta_fondo:
            self.canvas.delete(self.layer_tags["background"])
            self._background_item = None
            self._background_image = None
            return
        self._redibujar_fondo()

    def clear_layer(self, layer="content"):
        """Delete every canvas item in a named layer."""
        layer_tag = self._layer_tag(layer)
        self.canvas.delete(layer_tag)
        keys_to_forget = [
            key for key, item_layer in self._item_layers.items()
            if self._layer_tag(item_layer) == layer_tag
        ]
        for key in keys_to_forget:
            for ref_key in [k for k in self._image_refs if k == key or k.startswith(f"{key}:")]:
                self._image_refs.pop(ref_key, None)
            self._item_layers.pop(key, None)

    def clear_item(self, key):
        """Delete a logical item group by key."""
        self.canvas.delete(self._item_tag(key))
        for ref_key in [k for k in self._image_refs if k == key or k.startswith(f"{key}:")]:
            self._image_refs.pop(ref_key, None)
        self._item_layers.pop(key, None)

    def draw_rect(
        self,
        key,
        x,
        y,
        width,
        height,
        fill="",
        outline="",
        layer="content",
        tags=(),
        **kwargs,
    ):
        """Draw a rectangle in a logical item group."""
        self.clear_item(key)
        item_id = self.canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill=fill,
            outline=outline,
            tags=self._tags_for(key, layer, tags),
            **kwargs,
        )
        self._ordenar_capas()
        return item_id

    def draw_image(
        self,
        key,
        image,
        x,
        y,
        anchor="nw",
        layer="content",
        tags=(),
        **kwargs,
    ):
        """Draw a Tk image and keep a reference to avoid garbage collection."""
        self.clear_item(key)
        if not image:
            return None

        self._image_refs[key] = image
        item_id = self.canvas.create_image(
            x,
            y,
            image=image,
            anchor=anchor,
            tags=self._tags_for(key, layer, tags),
            **kwargs,
        )
        self._ordenar_capas()
        return item_id

    def draw_image_path(
        self,
        key,
        ruta,
        x=0,
        y=0,
        width=None,
        height=None,
        anchor="nw",
        layer="content",
        tags=(),
    ):
        """Load and draw an image path, optionally resized exactly."""
        if width is not None and height is not None:
            image = imagen_manager.cargar_imagen_exacta(ruta, (width, height))
        else:
            image = imagen_manager.cargar_imagen(ruta)
        return self.draw_image(key, image, x, y, anchor=anchor, layer=layer, tags=tags)

    def draw_full_image_path(self, key, ruta, layer="content", tags=()):
        """Draw an image path stretched exactly to the full canvas size."""
        width, height = self.size()
        if width < 2 or height < 2:
            return None
        return self.draw_image_path(
            key,
            ruta,
            x=0,
            y=0,
            width=width,
            height=height,
            anchor="nw",
            layer=layer,
            tags=tags,
        )

    def draw_text_block(
        self,
        key,
        text,
        x=None,
        y=None,
        width=None,
        fill=None,
        font=None,
        anchor="nw",
        layer="content",
        tags=(),
        **kwargs,
    ):
        """Draw a wrapped text block and replace any previous item with key."""
        self.clear_item(key)

        left, top, right, _bottom = self.padding
        canvas_width = max(self.canvas.winfo_width(), 1)
        x = left if x is None else x
        y = top if y is None else y
        width = width if width is not None else max(canvas_width - left - right, 1)

        item_tags = self._tags_for(key, layer, tags)
        item_id = self.canvas.create_text(
            x,
            y,
            text=text,
            fill=fill or COLORES["narrar"],
            font=font or ("Consolas", 11),
            anchor=anchor,
            width=width,
            tags=item_tags,
            **kwargs,
        )
        self._ordenar_capas()
        return item_id

    def draw_sprite_button(
        self,
        key,
        x,
        y,
        width,
        height,
        image=None,
        text="",
        command=None,
        active=True,
        layer="content",
        font=None,
        fill=None,
        disabled_fill=None,
        tags=(),
        background_fill=None,
        background_outline="",
        background_image=None,
    ):
        """Draw a clickable canvas button made from an optional sprite + label."""
        self.clear_item(key)

        item_tag = self._item_tag(key)
        item_tags = self._tags_for(key, layer, tags)
        fg = fill or COLORES["boton_activo"]
        disabled_fg = disabled_fill or COLORES["boton_inactivo"]
        text_fill = fg if active else disabled_fg

        if background_fill is not None or background_outline:
            self.canvas.create_rectangle(
                x,
                y,
                x + width,
                y + height,
                fill=background_fill or "",
                outline=background_outline,
                tags=item_tags,
            )

        if background_image:
            self._image_refs[f"{key}:background"] = background_image
            self.canvas.create_image(
                x + (width // 2),
                y + (height // 2),
                image=background_image,
                anchor="center",
                tags=item_tags,
            )

        if image:
            self._image_refs[key] = image
            image_y = y + (height // 2)
            if text:
                image_y -= 8
            self.canvas.create_image(
                x + (width // 2),
                image_y,
                image=image,
                anchor="center",
                tags=item_tags,
            )

        if text:
            text_y = y + height - 10 if image else y + (height // 2)
            self.canvas.create_text(
                x + (width // 2),
                text_y,
                text=text,
                fill=text_fill,
                font=font or ("Consolas", 10),
                anchor="center",
                tags=item_tags,
            )

        self._bind_button(item_tag, command, active)
        self._ordenar_capas()
        return item_tag

    def _programar_redibujado(self, _event=None):
        if self._resize_after_id:
            self.canvas.after_cancel(self._resize_after_id)
        self._resize_after_id = self.canvas.after(self.resize_delay_ms, self._redibujar)

    def _redibujar(self):
        self._resize_after_id = None
        self._redibujar_fondo()
        self._ordenar_capas()
        self._notificar_resize()

    def _redibujar_fondo(self):
        if not self._ruta_fondo:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 2 or height < 2:
            return

        img = imagen_manager.cargar_imagen_exacta(self._ruta_fondo, (width, height))
        if not img:
            return

        self._background_image = img
        bg_tag = self.layer_tags["background"]
        if self._background_item is None:
            self._background_item = self.canvas.create_image(
                0,
                0,
                image=img,
                anchor="nw",
                tags=("background", bg_tag),
            )
        else:
            self.canvas.itemconfig(self._background_item, image=img)
        self._ordenar_capas()

    def _ordenar_capas(self):
        for tag in CANVAS_LAYER_ORDER:
            self.canvas.tag_raise(tag)
        self.canvas.tag_lower(self.layer_tags["background"])

    def _notificar_resize(self):
        size = self.size()
        if size == self._last_size:
            return
        self._last_size = size
        for callback in tuple(self._resize_callbacks):
            callback(self)

    def _bind_button(self, item_tag, command, active):
        self.canvas.tag_unbind(item_tag, "<Button-1>")
        self.canvas.tag_unbind(item_tag, "<Enter>")
        self.canvas.tag_unbind(item_tag, "<Leave>")

        if not command or not active:
            return

        self.canvas.tag_bind(item_tag, "<Button-1>", lambda _event: command())
        self.canvas.tag_bind(item_tag, "<Enter>", lambda _event: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind(item_tag, "<Leave>", lambda _event: self.canvas.configure(cursor=""))

    def _tags_for(self, key, layer, tags):
        self._item_layers[key] = layer
        base_tags = (self._layer_tag(layer), self._item_tag(key))
        if isinstance(tags, str):
            return base_tags + (tags,)
        return base_tags + tuple(tags)

    def _layer_tag(self, layer):
        return self.layer_tags.get(layer, layer)

    @staticmethod
    def _item_tag(key):
        return f"item:{key}"

    @staticmethod
    def _normalizar_padding(padding):
        if padding is None:
            return (0, 0, 0, 0)
        if isinstance(padding, int):
            return (padding, padding, padding, padding)
        if len(padding) == 2:
            horizontal, vertical = padding
            return (horizontal, vertical, horizontal, vertical)
        if len(padding) == 4:
            return tuple(padding)
        return (0, 0, 0, 0)
