#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

def is_void_element(tag_name):
    void_elements = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]
    return tag_name in void_elements
   
def render_attributes(attributes):
    sorted_attributes = sorted(attributes.items(), key=lambda x: x[0])
    result = ""
    for k,v in sorted_attributes:
        if v is None:
            result += f" {k}"
        else:
            result += f" {k}=\"{v}\""
    return result

def render(token, text):
    if token['type'] == "OPEN":
        attributes = render_attributes(token['attributes'])
        return f"<{token['tag_name']}{attributes}>"
    if token['type'] == "OPEN_SELF_CLOSING":
        attributes = render_attributes(token['attributes'])
        return f"<{token['tag_name']}{attributes}>"
    if token['type'] == "CLOSE":
        return f"</{token['tag_name']}>"
    if token['type'] == "WHITESPACE":
        return text
    if token['type'] == "INNER_TEXT":
        return text
    if token['type'] == "COMMENT":
        return text
    raise Exception(f"Don't know how to render token type {token['type']}")

def top_of_stack(stack):
    if len(stack) < 1:
        return None
    return stack[-1]

def tokenize(inp):
    tokens = [{"type": None, "start": 0}]
    state = None
    token_start = -1
    tag_name_buffer = ""
    attribute_key_buffer = ""
    attribute_value_buffer = ""
    attributes = {}
    count = 0
    for ch in inp:
        if state is None:
            if ch == "<":
                token_start = count
                state = "OPEN"
        elif state == "OPEN":
            if re.match("[a-zA-Z]", ch):
                tag_name_buffer = ch
                attributes = {}
                state = "OPENING_TAG"
            elif ch == "/":
                state = "CLOSING"
            elif ch == "!":
                tag_name_buffer = ch
                state = "EXCLAMATION"
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "OPENING_TAG":
            if re.match("[a-zA-Z-0-9]", ch):
                tag_name_buffer += ch
            elif re.match("\\s", ch):
                state = "ATTRIBUTES"
            elif ch == "/":
                state = "SELF_CLOSING"
            elif ch == ">":
                tokens.append({"type": "OPEN", "tag_name": tag_name_buffer, "attributes": attributes, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "ATTRIBUTES":
            if re.match("[a-zA-Z-]", ch):
                attribute_key_buffer = ch
                state = "ATTRIBUTE_KEY"
            elif re.match("\\s", ch):
                pass
            elif ch == "/":
                state = "SELF_CLOSING"
            elif ch == ">":
                tokens.append({"type": "OPEN", "tag_name": tag_name_buffer, "attributes": attributes, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "SELF_CLOSING":
            if ch == ">":
                tokens.append({"type": "OPEN_SELF_CLOSING", "tag_name": tag_name_buffer, "attributes": attributes, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "ATTRIBUTE_KEY":
            if re.match("[a-z0-9A-Z-]", ch):
                attribute_key_buffer += ch
            elif ch == "=":
                attribute_value_buffer = ""
                state = "ATTRIBUTE_VALUE"
            elif re.match("\\s", ch):
                attributes[attribute_key_buffer] = None
                state = "ATTRIBUTES"
            elif ch == "/":
                attributes[attribute_key_buffer] = None
                state = "SELF_CLOSING"
            elif ch == ">":
                attributes[attribute_key_buffer] = None
                tokens.append({"type": "OPEN", "tag_name": tag_name_buffer, "attributes": attributes, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "ATTRIBUTE_VALUE":
            if ch == "'":
                state = "ATTRIBUTE_VALUE_SINGLE"
            elif ch == "\"":
                state = "ATTRIBUTE_VALUE_DOUBLE"
            elif ch == ">":
                attributes[attribute_key_buffer] = attribute_value_buffer
                tokens.append({"type": "OPEN", "tag_name": tag_name_buffer, "attributes": attributes, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif re.match("\\s", ch):
                attributes[attribute_key_buffer] = attribute_value_buffer
                state = "ATTRIBUTES"
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                attribute_value_buffer += ch
        elif state == "ATTRIBUTE_VALUE_DOUBLE":
            if ch == "\"":
                attributes[attribute_key_buffer] = attribute_value_buffer
                state = "ATTRIBUTES"
            else:
                attribute_value_buffer += ch
        elif state == "ATTRIBUTE_VALUE_SINGLE":
            if ch == "'":
                attributes[attribute_key_buffer] = attribute_value_buffer
                state = "ATTRIBUTES"
            else:
                attribute_value_buffer += ch
        elif state == "CLOSING":
            if re.match("[a-zA-Z]", ch):
                tag_name_buffer = ch
                state = "CLOSING_TAG"
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "CLOSING_TAG":
            if re.match("[a-zA-Z-0-9]", ch):
                tag_name_buffer += ch
                state = "CLOSING_TAG"
            elif re.match("\\s", ch):
                state = "CLOSING_TAG_GAP"
            elif ch == ">":
                tokens.append({"type": "CLOSE", "tag_name": tag_name_buffer, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "CLOSING_TAG_GAP":
            if re.match("\\s", ch):
                pass
            elif ch == ">":
                tokens.append({"type": "CLOSE", "tag_name": tag_name_buffer, "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "EXCLAMATION":
            if re.match("[a-zA-Z]", ch):
                tag_name_buffer += ch
                state = "OPENING_TAG"
            elif ch == "-":
                state = "DASH_1"
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "DASH_1":
            if ch == "-":
                state = "COMMENT"
            elif ch == "<":
                token_start = count
                state = "OPEN"
            else:
                state = None
        elif state == "COMMENT": 
            if ch == "-":
                state = "END_DASH_1"
        elif state == "END_DASH_1":
            if ch == "-":
                state = "END_DASH_2"
            else:
                state = "COMMENT"
        elif state == "END_DASH_2":
            if ch == ">":
                tokens.append({"type": "COMMENT", "start": token_start})
                tokens.append({"type": None, "start": count+1})
                state = None
            else:
                state = "COMMENT"
        count += 1

    tokens.append({"type": None, "start": count})
    return tokens


def render_doc(tokens, inp):
    ws = " "
    output = ""
    render_stack = []
    for i in range(len(tokens)-1):
        token = tokens[i]
        x,y = token["start"], tokens[i+1]["start"]
        if x == y:
            continue

        if token['type'] is None:
            if re.match("^\\s*$", inp[x:y]):
                token['type'] = "WHITESPACE"
            else:
                token['type'] = "INNER_TEXT"
        elif token['type'] == "OPEN_SELF_CLOSING" and is_void_element(token['tag_name']):
            token['type'] = "OPEN"
       
        if token['type'] == "OPEN":
            rendered = render(token, inp[x:y])
            if token['tag_name'] in ["pre", "code", "style", "script"]:
                output += ws*len(render_stack)+rendered
                render_stack.append(token['tag_name'])
            elif top_of_stack(render_stack) in ["pre", "code", "style", "script"]:
                output += inp[x:y]
            elif is_void_element(token['tag_name']):
                output += ws*len(render_stack)+rendered+"\n"
            elif token['tag_name'] == "!DOCTYPE":
                output += (ws*len(render_stack)+rendered+"\n")
            else:
                output += ws*len(render_stack)+rendered+"\n"
                render_stack.append(token['tag_name'])
        elif token['type'] == "OPEN_SELF_CLOSING":
            if top_of_stack(render_stack) in ["pre", "code", "style", "script"]:
                output += inp[x:y]
            else:
                rendered = render(token, inp[x:y])
                output += ws*len(render_stack)+rendered+"\n"
                output += ws*len(render_stack)+f"</{token['tag_name']}>"+"\n"
        elif token['type'] == "CLOSE":
            if token['tag_name'] in ["pre", "code", "style", "script"]:
                rendered = render(token, inp[x:y])
                popped = render_stack.pop()
                if popped != token['tag_name']:
                    raise Exception(f"Expected </{popped}> but have </{token['tag_name']}> vim: ':normal! 0go{token['start']} \"'")
                output += rendered+"\n"
            elif top_of_stack(render_stack) in ["pre", "code", "style", "script"]:
                output += inp[x:y]
            elif is_void_element(token['tag_name']):
                pass
            else:
                rendered = render(token, inp[x:y])
                popped = render_stack.pop()
                if popped != token['tag_name']:
                    raise Exception(f"Expected </{popped}> but have </{token['tag_name']}> vim: ':normal! 0go{token['start']} \"'")
                output += ws*len(render_stack)+rendered+"\n"
        elif token['type'] == "WHITESPACE":
            if top_of_stack(render_stack) in ["pre", "code", "style", "script"]:
                output += inp[x:y]
        elif token['type'] == "INNER_TEXT":
            if top_of_stack(render_stack) in ["pre", "code", "style", "script"]:
                output += inp[x:y]
            else:
                lines = inp[x:y].strip().split('\n')
                for line in lines:
                    output += ws*len(render_stack)+line.strip()+"\n"
        elif token['type'] == "COMMENT":
            rendered = render(token, inp[x:y])
            output += ws*len(render_stack)+rendered+"\n"

    if len(render_stack) > 0:
        raise Exception(f"</{render_stack[-1]}> is missing")
    
    return output

def main(reader):
    inp = "".join(list(reader.read()))
    tokens = tokenize(inp)
    output = render_doc(tokens, inp)
    return output

if __name__ == "__main__":
    if len(sys.argv[1:]) > 0:
        try:
            for filename in sys.argv[1:]:
                with open(filename, 'r+') as f:
                    result = main(f)
                    f.seek(0)
                    f.write(result)
                    f.truncate()
                    f.close()
        except Exception as err:
            raise Exception(f"{filename}: {err}")
    else:
        print(main(sys.stdin))
