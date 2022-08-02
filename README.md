# splitgcode

Splits an input gcode file into multiple sections for manual material changes.

## Usage

### Config

You can change a few settings in the file `splitgcode.yaml`

```yaml
layers:
  format: ";LAYER:{}"
  footer: "M104 S0 ;Extruder heater off"
debug: false
```

* layers: Layer related configuration
** format: Format string to use when recognizing layers. If your slicer uses a different comment format at the start of every layer, change this to match
** footer: The first line after the last layer in your file.
* debug: If `true`, additional debug info will be printed.

### Commands

```bash
pip install -r requirements.txt # Install required dependencies
python spitgcode.py -i test.gcode -l 3 -l 7 # Split test.gcode into 2 sections (layers 0-2 and 3-6)
python spitgcode.py -i test.gcode -l 1 -l 6 -l 7 # Split test.gcode into 3 sections (layers 0, 2-5, and 6)
python spitgcode.py -i test.gcode -l 6 -l 7 -o custom_top # Split test.gcode into 2 sections (layers 0-5, and 6) and save the output in "custom_top.section*.gcode"
```
