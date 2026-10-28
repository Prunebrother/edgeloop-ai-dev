# SPDX-License-Identifier: AGPL-3.0-only
"""Version 1 presentation envelope. Never accepts user text or session commands."""
EXPRESSIONS = ('neutral', 'happy', 'playful', 'flirty', 'mischievous', 'focused',
               'excited', 'surprised', 'disappointed', 'concerned', 'proud', 'comforting')
FORMAT_INSTRUCTION = (
    'Output format v1: begin your reply with exactly one [[expression:ID]] header. '
    'The word expression is literal: for example [[expression:happy]]. Never put a number in the header. '
    'Choose ID from: ' + ', '.join(EXPRESSIONS) + '. '
    'Then give your normal dialogue in your established character. '
    'The header describes your intended delivery, never the user or session state. '
    'Do not explain the header or narrate a facial gesture for this format.')


class ExpressionStream:
    """Bounded scanner: headers removed anywhere, only first leading header trusted.

    Retains at most 64 prefix characters. Oversized envelopes are discarded through
    closing delimiter/newline. Legacy prose streams as soon as it diverges from a
    reserved prefix. Inline legacy reasoning is suppressed before presentation.
    """
    tokens = ('[[expression:', '<think>', '</think>') + tuple('[[' + e + ':' for e in EXPRESSIONS)

    def __init__(self, on_expression=None, enabled=True):
        self.pending = ''
        self.mode = 'text'
        self.envelope = ''
        self.tail = ''
        self.expression = None
        self.valid = None
        self.leading = True
        self.headers = 0
        self.canonical_header = False
        self.on_expression = on_expression
        self.enabled = enabled

    def feed(self, text):
        output = []
        for char in text:
            if self.mode == 'metadata':
                self.tail = (self.tail + char)[-2:]
                if len(self.envelope) < 64:self.envelope += char
                else:self.valid = False
                if self.tail == ']]' or char == '\n':
                    candidate = self.envelope[:-2] if self.tail == ']]' else ''
                    valid = self.canonical_header and candidate in EXPRESSIONS and self.valid is not False
                    if self.headers == 1:
                        self.valid = valid
                        if valid and self.leading and self.enabled:
                            self.expression = candidate
                            if self.on_expression:self.on_expression(candidate)
                    self.mode = 'text';self.envelope = '';self.tail = ''
                continue
            if self.mode == 'reasoning':
                self.tail = (self.tail + char)[-8:]
                if self.tail.lower().endswith('</think>'):
                    self.mode = 'text';self.tail = ''
                continue
            self.pending += char
            while self.pending:
                lower = self.pending.lower()
                if lower.startswith('[[') and lower in self.tokens:
                    self.canonical_header = lower == '[[expression:'
                    self.headers += 1
                    self.mode = 'metadata';self.pending = '';self.envelope = '';self.tail = ''
                    break
                if lower == '<think>':
                    self.mode = 'reasoning';self.pending = '';self.tail = ''
                    break
                if lower == '</think>':
                    self.pending = '';break
                if any(token.startswith(lower) for token in self.tokens):break
                visible = self.pending[0];self.pending = self.pending[1:]
                output.append(visible)
                if not visible.isspace():self.leading = False
        return ''.join(output)

    def finish(self):
        # A partial reserved prefix must never reach dialogue or memory.
        self.pending = ''
        if self.mode == 'metadata':self.valid = False
        return ''


def clean_dialogue(text):
    parser = ExpressionStream(enabled=False)
    return (parser.feed(text) + parser.finish()).strip()
