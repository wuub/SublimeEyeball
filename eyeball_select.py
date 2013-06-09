import json
import subprocess
import sublime
import sublime_plugin

LAST_BLOCKS = {}
LAST_SELECTION = {}
CUR_BLOCK = {}


def _code_blocks(python, code, line):
    p = subprocess.Popen(
        [python, '-m', 'eyeball', '--line', str(line)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate(code.encode('utf-8'))  #pylint: disable=W0612

    res = out.decode('utf-8')
    blocks = json.loads(res)

    return blocks


def code_blocks(code, line):
    for python in sublime.load_settings("Eyeball.sublime-settings").get('pythons', []):
        try:
            return  _code_blocks(python, code, line)
        except (ValueError, FileNotFoundError) as e:
            print ("SublimeEyeball", python, e)
            pass
    return None


class EyeballSelectCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def cycle_blocks(self, idx):
        CUR_BLOCK[idx] += 1
        CUR_BLOCK[idx] %= len(LAST_BLOCKS[idx])
        v = self.view
        block = LAST_BLOCKS[idx][CUR_BLOCK[idx]]
        start = v.text_point(block['start'] - 1, 0)
        end = v.text_point(block['end'], 0)
        LAST_SELECTION[idx] = sublime.Region(start, end)
        v.sel().add(LAST_SELECTION[idx])

    def run(self, edit):
        if not self.view.score_selector(0, 'source.python'):
            return
        selections = list(self.view.sel())
        self.view.sel().clear()
        for idx, sel in enumerate(selections):
            self.handle(idx, sel)
        if len(self.view.sel()) == 0:
            for sel in selections:
                self.view.sel().add(sel)

    def handle(self, idx, sel):
        v = self.view

        if sel == LAST_SELECTION.get(idx):
            self.cycle_blocks(idx)
            return

        code = v.substr(sublime.Region(0, v.size()))
        (row, _col) = v.rowcol(sel.begin())

        blocks = code_blocks(code, row + 1)
        if not blocks:
            return

        LAST_BLOCKS[idx] = blocks
        CUR_BLOCK[idx] = -1
        self.cycle_blocks(idx)

