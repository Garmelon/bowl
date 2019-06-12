from typing import Optional, Tuple

import urwid

__all__ = ["EditWidget", "PasswordEditWidget"]

class EditWidget(urwid.WidgetWrap):

    def __init__(self,
            prompt: str,
            caption: str = "",
            style: Optional[str] = None,
            ) -> None:

        self._prompt = urwid.Text(prompt, align=urwid.CENTER)
        self._edit = urwid.Edit(caption=caption, align=urwid.CENTER)

        if style is None:
            self._edit_wrap = self._edit
        else:
            self._edit_wrap = urwid.AttrMap(self._edit, style)

        self._pile = urwid.Pile([
            (urwid.PACK, self._prompt),
            (urwid.PACK, self._edit_wrap),
        ])
        super().__init__(self._pile)

    @property
    def width(self) -> int:
        prompt_width, _ = self._prompt.pack(None)
        edit_width, _ = self._edit.pack(None)
        return max(prompt_width, edit_width)

    @property
    def text(self) -> str:
        return self._edit.edit_text

class PasswordEditWidget(urwid.WidgetWrap):

    def __init__(self,
            prompt: str,
            mask_char: str = "*",
            style: Optional[str] = None,
            ) -> None:

        self._mask_char = mask_char

        self._prompt = urwid.Text(prompt, align=urwid.CENTER)
        self._edit = urwid.Edit(align=urwid.CENTER)
        self._fake_edit = urwid.Edit(align=urwid.CENTER)

        if style is None:
            self._fake_edit_wrap = self._fake_edit
        else:
            self._fake_edit_wrap = urwid.AttrMap(self._fake_edit, style)

        self._pile = urwid.Pile([
            (urwid.PACK, self._prompt),
            (urwid.PACK, self._fake_edit_wrap),
        ])
        super().__init__(self._pile)

    @property
    def width(self) -> int:
        prompt_width, _ = self._prompt.pack(None)
        edit_width, _ = self._edit.pack(None)
        return max(prompt_width, edit_width)

    @property
    def text(self) -> str:
        return self._edit.edit_text

    def update_fake_edit(self) -> None:
        fake_text = self._mask_char * len(self._edit.edit_text)
        self._fake_edit.edit_text = fake_text
        self._fake_edit.edit_pos = self._edit.edit_pos

    def keypress(self, size: Tuple[int], key: str) -> Optional[str]:
        key = self._edit.keypress(size, key)
        self.update_fake_edit()
        return key
