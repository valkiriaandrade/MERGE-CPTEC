import matplotlib
import pytest

matplotlib.use("Agg")

from matplotlib.colors import ListedColormap, to_hex  # noqa: E402

from merge_cptec.colour_scales import (  # noqa: E402
    RAINFALL_COLOURS,
    SPREAD_LABELS,
    colour_scale,
)


@pytest.mark.parametrize(
    ("product", "region"), [("accumulation", "north"), ("climatology", "brazil")]
)
def test_original_rainfall_scale(product, region):
    scale = colour_scale(product, region)
    assert scale.levels == (0, 10, 20, 30, 40, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500)
    assert isinstance(scale.cmap, ListedColormap)
    assert [to_hex(c).upper() for c in scale.cmap.colors] == list(RAINFALL_COLOURS)
    assert scale.cmap.N == len(scale.levels) - 1
    assert scale.extend == "max"


def test_original_brazil_accumulation_scale():
    scale = colour_scale("accumulation", "brazil")
    assert scale.levels == (0, 20, 50, 80, 100, 150, 200, 300, 400, 500)
    assert scale.cmap.name.startswith("rainbow_r")
    assert scale.cmap.N == 9
    assert scale.extend == "max"


def test_anomaly_scales():
    assert colour_scale("anomaly").cmap == "BrBG"
    spread = colour_scale("anomaly-spread")
    assert spread.cmap.N == 5 == len(spread.class_labels)
    assert spread.class_labels == SPREAD_LABELS


def test_unknown_product():
    with pytest.raises(ValueError, match="colour scale"):
        colour_scale("unknown")


def test_class_labels_on_map(tmp_path):
    import geopandas as gpd
    from shapely.geometry import box

    from merge_cptec.plotting import plot_map

    borders = tmp_path / "bounds.geojson"
    gpd.GeoDataFrame(geometry=[box(-2, -2, 2, 2)], crs=4326).to_file(borders)
    spread = colour_scale("anomaly-spread")
    output = tmp_path / "spread.png"
    plot_map(
        [[1.0, 2.0], [3.0, 8.0]],
        [-1, 1],
        [-1, 1],
        output,
        title="Test",
        label="class",
        levels=spread.levels,
        cmap=spread.cmap,
        shapefile=borders,
        spatial_spread=True,
        class_labels=spread.class_labels,
    )
    assert output.read_bytes().startswith(b"\x89PNG")
