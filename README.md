# splitgcode

Splits an input gcode file into multiple sections for manual material changes.

## Usage

```bash
pip install -r requirements.txt # Install required dependencies
python spitgcode.py -i test.gcode -l 3 -l 7 # Split test.gcode into 2 sections (layers 0-2 and 3-6)
python spitgcode.py -i test.gcode -l 1 -l 6 -l 7 # Split test.gcode into 3 sections (layers 0, 2-5, and 6)
python spitgcode.py -i test.gcode -l 6 -l 7 -o custom_top # Split test.gcode into 2 sections (layers 0-5, and 6) and save the output in "custom_top.section*.gcode"
```
