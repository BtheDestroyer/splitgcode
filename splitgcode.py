import yaml
from enum import Enum
import argparse

cfg = yaml.load(open("./splitgcode.yaml").read(), yaml.Loader)
debug_log = lambda *obj : None
if "debug" in cfg and cfg["debug"]:
    debug_log = lambda *obj : print(*obj)
debug_log("Debugging Enabled!")

debug_log("config:", cfg)

class PositionMode(Enum):
    ABSOLUTE = 0
    RELATIVE = 1

class GCodeSimulator:
    # GCode interpreters
    def __handler_G0(self, arguments : list):
        for arg in arguments:
            if arg.startswith("X"):
                if self.positioning_mode == PositionMode.ABSOLUTE:
                    self.x = float(arg[1:])
                elif self.positioning_mode == PositionMode.RELATIVE:
                    self.x += float(arg[1:])
                else:
                    raise Exception("Invalid current positioning mode: {}".format(self.positioning_mode))
                continue
            if arg.startswith("Y"):
                if self.positioning_mode == PositionMode.ABSOLUTE:
                    self.y = float(arg[1:])
                elif self.positioning_mode == PositionMode.RELATIVE:
                    self.y += float(arg[1:])
                else:
                    raise Exception("Invalid current positioning mode: {}".format(self.positioning_mode))
                continue
            if arg.startswith("Z"):
                if self.positioning_mode == PositionMode.ABSOLUTE:
                    self.z = float(arg[1:])
                elif self.positioning_mode == PositionMode.RELATIVE:
                    self.z += float(arg[1:])
                else:
                    raise Exception("Invalid current positioning mode: {}".format(self.positioning_mode))
                continue
            if arg.startswith("E"):
                if self.extrusion_mode == PositionMode.ABSOLUTE:
                    self.e = float(arg[1:])
                elif self.extrusion_mode == PositionMode.RELATIVE:
                    self.e += float(arg[1:])
                else:
                    raise Exception("Invalid current extrusion mode: {}".format(self.positioning_mode))
                continue
    
    __handler_G1 = __handler_G0

    def __handler_G90(self, arguments : list):
        self.positioning_mode = PositionMode.ABSOLUTE

    def __handler_G91(self, arguments : list):
        self.positioning_mode = PositionMode.RELATIVE

    def __handler_M82(self, arguments : list):
        self.extrusion_mode = PositionMode.ABSOLUTE

    def __handler_M83(self, arguments : list):
        self.extrusion_mode = PositionMode.RELATIVE

    # User-facing API
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_layer = -1
        self.current_line = -1
        self.code_header_end = -1
        self.code_layer_starts = []
        self.code_layer_positions = []
        self.code_layer_extrusions = []
        self.code_layer_ends = []
        self.code_footer_start = -1
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.e = 0.0
        self.positioning_mode = PositionMode.ABSOLUTE
        self.extrusion_mode = PositionMode.ABSOLUTE

    def run(self, line : str):
        self.current_line += 1
        if line.strip() == cfg["layers"]["format"].format(self.current_layer + 1):
            if self.current_layer == -1:
                self.code_header_end = self.current_line
            else:
                self.code_layer_ends.append(self.current_line)
            self.current_layer += 1
            self.code_layer_starts.append(self.current_line)
            self.code_layer_positions.append([self.x, self.y, self.z])
            self.code_layer_extrusions.append(self.e)
        elif line.strip() == cfg["layers"]["footer"]:
            self.code_layer_ends.append(self.current_line)
            self.code_footer_start = self.current_line
        line = line[:line.find(";")]
        split_line = line.split()
        if len(split_line) == 0:
            return
        try:
            handler_name = "_{}__handler_{}".format(self.__class__.__name__, split_line[0])
            handler = getattr(self, handler_name)
            handler(split_line[1:])
        except AttributeError:
            # This may happen; nothing to be done
            pass
        except Exception:
            print("Error when running gcode line {}: {}".format(self.current_line, line))
            raise

    def read_file(self, gcode_path : str):
        self.reset()
        file = open(gcode_path)
        for line in file:
            self.run(line)

class GCodeSections:
    def __init__(self, gcode_path : str, gcode_sim : GCodeSimulator):
        file = open(gcode_path)
        current_line = 0
        current_layer = -1
        self.header = ""
        self.layers = []
        self.layer_positions = gcode_sim.code_layer_positions
        self.layer_extrusions = gcode_sim.code_layer_extrusions
        self.footer = ""
        debug_log("Reading layers...")
        debug_log("  Reading header...")
        for line in file:
            if current_line < gcode_sim.code_header_end:
                self.header += line
            elif current_line == gcode_sim.code_header_end:
                current_layer += 1
                self.layers.append("")
                debug_log("  Reading layer {}...".format(current_layer))
            if current_layer >= 0 and current_layer < len(gcode_sim.code_layer_starts):
                if current_line >= gcode_sim.code_layer_ends[current_layer]:
                    current_layer += 1
                    if current_layer < len(gcode_sim.code_layer_starts):
                        self.layers.append("")
                        debug_log("  Reading layer {}...".format(current_layer))
                    else:
                        debug_log("  Reading footer...")
            if current_layer >= 0 and current_layer < len(gcode_sim.code_layer_starts):
                if current_line >= gcode_sim.code_layer_starts[current_layer] and current_line < gcode_sim.code_layer_ends[current_layer]:
                    self.layers[current_layer] += line
            if current_line >= gcode_sim.code_footer_start:
                self.footer += line
            current_line += 1
    
    def write(self, out_path_base : str, section_layers : list):
        current_section = 0
        current_layer = 0
        for section_end in section_layers:
            path = "{}.section{}.gcode".format(out_path_base, current_section)
            print("Writing section file:", path)
            file = open(path, "w")
            file.write(self.header)
            file.write("; Split with splitgcode.py by Bryce Dixon\n")
            file.write("; https://github.com/BtheDestroyer/splitgcode\n")
            file.write("; Split section {} (layers {}-{})\n".format(current_section, current_layer, section_end - 1))
            if current_layer != 0:
                file.write("G92 E{} ; Set current extrusion to continue where we left off\n".format(self.layer_extrusions[current_layer]))
                file.write("G0 F1200 Z{} ; Go up a bit before starting the layer\n".format(self.layer_positions[current_layer][2] + 2))
                file.write("G0 X{} Y{} ; Go over where the layer should start\n".format(self.layer_positions[current_layer][0], self.layer_positions[current_layer][1]))
                file.write("G0 Z{} ; Lower down to start the layer\n".format(self.layer_positions[current_layer][2]))
            for layer in range(current_layer, section_end):
                file.write(self.layers[layer])
            file.write(self.footer)
            current_layer = section_end
            current_section += 1

# Set up options and parameters
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Gcode file to split", default=None, action="store", type=str)
    parser.add_argument("-o", "--output", help="Base-name for the split output files", default=None, action="store", type=str)
    parser.add_argument("-l", "--layer", help="Last layer for each section", default=[], dest="layers", action="append", type=int)
    args = parser.parse_args()
    debug_log("args:", args)
    if args.input == None:
        print("No input file given. Run with --help for usage.")
        exit(-1)
    if len(args.layers) == 0:
        print("No section layers given. Run with --help for usage.")
        exit(-2)
    print("Parsing file:", args.input)
    gcode_sim = GCodeSimulator()
    gcode_sim.reset()
    gcode_sim.read_file(args.input)
    debug_log("Parsing done!")
    debug_log("gcode_sim:", vars(gcode_sim))
    gcode_sections = GCodeSections(args.input, gcode_sim)
    args.layers.sort()
    debug_log("Section layers:", args.layers)
    gcode_sections.write(args.output if args.output != None else args.input[:args.input.rfind(".")], args.layers)
