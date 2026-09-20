from .arguments import execute, parser
from .io import files_in, read_field, save_netcdf, spatial
from .plotting import plot_map
from .processing import accumulate, anomaly


def run(args):
    if args.product == "anomaly-netcdf":
        if not args.climatology:
            raise ValueError("Informe --climatology")
        save_netcdf(anomaly(files_in(args.input, ".grib2"), args.climatology), args.output)
        return
    if args.product == "accumulation":
        values, lat, lon = accumulate(files_in(args.input, ".grib2"))
    else:
        variable = "precacum" if args.product == "climatology" else "anomalia_precipitacao"
        field = spatial(read_field(args.input, variable))
        values, lat, lon = field.values, field.lat.values, field.lon.values
    is_anomaly = args.product.startswith("anomaly")
    levels = (
        [-400, -300, -200, -100, -75, -50, -25, -5, 0, 5, 25, 50, 75, 100, 200, 300, 400]
        if is_anomaly
        else [0, 20, 50, 80, 100, 150, 200, 300, 400, 500]
    )
    plot_map(
        values,
        lat,
        lon,
        args.output,
        title=args.title or args.product,
        label="Anomalia (mm)" if is_anomaly else "Precipitação (mm)",
        levels=levels,
        cmap="BrBG" if is_anomaly else "YlGnBu",
        shapefile=args.shapefile,
        spatial_spread=args.product == "anomaly-spread",
        states=["AC", "AP", "AM", "PA", "RO", "RR", "TO"] if args.region == "norte" else None,
        extent=[-75, -44, -19, 7] if args.region == "norte" else [-75, -34, -35, 7],
    )


def main(argv=None):
    p = parser("Acumulados e anomalias MERGE; forneça apenas os dias do período desejado")
    p.add_argument("--input", required=True)
    p.add_argument("--climatology")
    p.add_argument("--region", choices=["brasil", "norte"], default="brasil")
    p.add_argument(
        "--product",
        choices=["accumulation", "anomaly-netcdf", "anomaly", "anomaly-spread", "climatology"],
        default="accumulation",
    )
    execute(p, run, argv)
