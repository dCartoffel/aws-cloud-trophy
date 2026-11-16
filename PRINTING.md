# Cloud Innovation Challenge trophy: print guide

The trophy is a cloud with a traffic spike cut through it, standing on its flat bottom. Two 14 mm tabs under the cloud sit 4 mm deep in slots in a two-step plinth (126 × 46 × 6 mm lower step, 112 × 34 × 10 mm upper step). Overall it is 126 × 46 × 73 mm.

All print files are in `models/`. Recommended: print the **kit** (cloud + plinth). Neither part needs supports.

| File | Orientation | Notes |
|---|---|---|
| `cloud_trophy_symbol.stl` | Flat, as exported (back face on the bed) | 92 × 61 × 8 mm including tabs, about 30 cm³ |
| `cloud_trophy_base.stl` | Flat, as exported | Two-step plinth, 126 × 46 × 16 mm, with two slots, about 70 cm³ |
| `cloud_trophy_base_2colour.3mf` | Same as the plinth | Plinth and label as two objects, for an AMS/MMU |
| `cloud_trophy_label_inlay.stl` | Optional | Label fill on its own |
| `cloud_trophy_onepiece.stl` | Upright | Fused version. The cloud's outline is self-supporting, but the top edges of the spike cut-out bridge, so expect a little sag there or add supports. |

## Slicer settings (PLA or PETG, 0.4 mm nozzle)

- **Layer height:** 0.2 mm.
- **Walls:** 4 perimeters.
- **Top layers:** 5 or more.
- **Infill:** 15–20 % for the cloud. Use 30 % or more for the plinth, so the trophy has some weight.
- **Seam:** "Rear" (or "Back").
- **Brim:** not needed. The plinth's bed edge has a 0.5 mm chamfer, and the cloud's back face has a 0.4 mm step.
- **Ironing:** optional, on the plinth's top face and on the cloud's front, which prints as its top face.

Colour suggestion: an orange or white cloud on a dark navy or black plinth.

## Two-colour label (engraved 0.6 mm into the top)

- **With an AMS/MMU:** open `cloud_trophy_base_2colour.3mf` and give the `label` object a contrasting filament.
- **Single extruder:** add a filament change (M600 / "pause at height") at the layer where the engraving starts, at Z = 15.4 mm. Load the second colour there. The top surface of the plinth then prints in the second colour, and the engraved letters show the first colour at their floor.
- Or print in one colour and fill the engraving with paint.

The default two-line label has a cap height of about 3.9 mm. Keep the second line short, or use one line, if you want bigger letters.

## Assembly

Test-fit the two tabs in their slots. The clearance is 0.15 mm per side, and each slot has a lead-in chamfer at the top. The slots are 0.4 mm deeper than the tabs, so the cloud's flat bottom rests on the plinth. Glue with CA or epoxy.

## Changing it

To change the label text, run:

`python make_trophy.py models "LINE ONE|LINE TWO"`

At the top of the script, `CLEAR` sets the fit, `PLINTH` and `STEP` set the sizes of the two steps, `TAB_W` and `TAB_X` set the tabs, and `SYM_Y` sets how far back the cloud stands.
