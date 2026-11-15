# Command+C (kitty.conf): copy kitty's own selection, like the default copy_or_noop. Without one, a window running
# tmux gets a made-up sequence that tmux turns into "copy from the Claude Code prompt" (tmux.conf, User1).
from kittens.tui.handler import result_handler


def main(args):
    pass


@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return
    if window.text_for_selection():
        window.copy_to_clipboard()
        return
    try:
        in_tmux = any('tmux' in ' '.join(p['cmdline']) for p in window.child.foreground_processes)
    except Exception:
        in_tmux = False
    if in_tmux:
        window.write_to_child(b'\x1b[9002~')
