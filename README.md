# EclosionDetector

`EclosionDetector` is a Python script for [Fiji](https://fiji.sc/) to detect eclosion events in *Drosophila melanogaster*.
The detection of eclosion events is based on the difference in brightness between a pupa and an empty pupal case. 
The latter is almost transparent while a late pupa is considerably darker.

# Usage

The script can be run from the Fiji script editor. First open the stack you want to analyze. This can be a video or an image sequence.

You can define the frame (`start_slice`) that is used to detect the pupae. The pupae should be darker than the background (i.e. below `threshold`).

You can define the minimum (`min_area`) and maximum (`max_area`) area (in pixel) for a pupa manually or estimate it with `autoset_size()`.
Here you can set the minimum (`min_area_factor`) and maximum (`max_area_factor`) in relation to the median of all detections.

You can also define the range of frames (`idx_min` and `idx_max`) where eclosion events should be detected.

For each pupa the mean, median and mode grey values are calculated at every frame. By setting `diff_method` you select which method you want to apply to detect eclosion events.

The difference theshold in grey value for an eclosion event to be recognized is defined in `diff_hatch`.

With `check_error = True` you can try to identify and exclude invalid eclosion events (e.g. flies walking over pupae)

The time (i.e. frame) for each eclosion event and the position of the pupa are recorded and can be exported with `save_csv()` as a csv file for further analysis.

The script can create a mosaic of frames just before and after the eclosion events with `create_mosaic()`. This is useful for quality control and to exclude invalid detections.
You can set the number of frames before and after the event by `timewindow_hatch`, `mosaic_size` defines the width and height of a single tile in the mosaic.

![Flies eclosing from their pupal cases](docs/eclosion.gif)

**EclosionDetector** has been used here:

    @article{Bidell.2023,
        author = {Bidell, Daniel and Feige, Natalie-Danielle and Triphan, Tilman and Pauls, Dennis and Helfrich-Förster, Charlotte and Selcho, Mareike},
        title = {Immediate effects of light on circadian eclosion and locomotor activity depend on distinct sensory input pathways},
        year = {2023},
        doi = {10.1101/2023.04.21.537872},
        URL = {https://www.biorxiv.org/content/10.1101/2023.04.21.537872v2},
        eprint = {https://www.biorxiv.org/content/10.1101/2023.04.21.537872v2.full.pdf},
        journal = {bioRxiv}
	}		
