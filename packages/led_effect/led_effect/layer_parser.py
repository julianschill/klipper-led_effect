from . import layer_parser_lark


class TermTransformer(layer_parser_lark.Transformer):
    NUMBER = float
    RATE = float
    CUTOFF = float
    BLEND = str
    LAYER_NAME = str
    WORD = str
    CNAME = str
    palette = list

    @layer_parser_lark.v_args(inline=True)
    def ESCAPED_STRING(self, s):
        return s[1:-1].replace('\\"', '"')

    def float_triplet(self, triplet):
        return tuple(triplet)

    def palette_entry(self, children):
        return children[0]

    def hex(self, hex):
        return tuple([int(hexVal,16)/255.0 for hexVal in hex])

    def legacy_line(self, children):
        effect, rate, cutoff, blend, palette = children
        return {
            "effect": effect, "parameters": {"effectRate": rate, "effectCutoff": cutoff},
            "blend": blend, "palette": palette
        }

    def parameterized_line(self, children):
        effect, parameters, blend, palette = children

        params = {k: v for k, v in [
            (param.children[0], param.children[1]) for param in parameters.children]}

        return {
            "effect": effect, "blend": blend, "palette": palette, "parameters": params
        }


layer_line_parser = layer_parser_lark.Lark_StandAlone()




def parse(line):
    tree = TermTransformer().transform(layer_line_parser.parse(line))
    return tree.children[0]
    
