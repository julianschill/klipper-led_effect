from . import layer_parser_lark



class TermTransformer(layer_parser_lark.Transformer):
    NUMBER = float
    RATE = float
    CUTOFF = float
    BLEND = str
    LAYER_NAME = str
    WORD = str
    CNAME = str
    
    @layer_parser_lark.v_args(inline=True)
    def ESCAPED_STRING(self, s):
        return s[1:-1].replace('\\"', '"')


layer_line_parser = layer_parser_lark.Lark_StandAlone()


def parse(line):
    tree = TermTransformer().transform(layer_line_parser.parse(line))

    if tree.children[0].data == "legacy_line":
        effect, rate, cutoff, blend, palette = tree.children[0].children
        palette = [tuple([color for color in entry.children if color != None])
                   for entry in palette.children]
        return {
            "effect": effect, "parameters": {"effectRate": rate, "effectCutoff": cutoff},
            "blend": blend, "palette": palette
        }
    elif tree.children[0].data == "parameterized_line":
        effect, parameters, blend, palette = tree.children[0].children

        params = {k: v for k, v in [
            (param.children[0], param.children[1]) for param in parameters.children]}
        
        palette = [tuple([color for color in entry.children if color != None])
                   for entry in palette.children]
        return {
            "effect": effect, "blend": blend, "palette": palette, "parameters": params
        }
    return None
