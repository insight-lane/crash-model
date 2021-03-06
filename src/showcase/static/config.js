var config = [
        {
            id: "boston_bike",
            name: "Boston, Massachusetts, USA (bike)",
            latitude: 42.3600825,
            longitude: -71.0588801,
            speed_unit: "mph",
            file: "data/boston/preds_viz_bike.geojson",
            crashes: "data/boston/crashes_rollup_bike.geojson"
        },
        {
            id: "boston_pedestrian",
            name: "Boston, Massachusetts, USA (pedestrian)",
            latitude: 42.3600825,
            longitude: -71.0588801,
            speed_unit: "mph",
            file: "data/boston/preds_viz_pedestrian.geojson",
            crashes: "data/boston/crashes_rollup_pedestrian.geojson"
        },
        {
            id: "boston_vehicle",
            name: "Boston, Massachusetts, USA (vehicle)",
            latitude: 42.3600825,
            longitude: -71.0588801,
            speed_unit: "mph",
            file: "data/boston/preds_viz_vehicle.geojson",
            crashes: "data/boston/crashes_rollup_vehicle.geojson"
        },
        {
            id: "cambridge_bike",
            name: "Cambridge, Massachusetts, USA (bike)",
            latitude: 42.3736158,
            longitude: -71.10973349999999,
            speed_unit: "mph",
            file: "data/cambridge/preds_viz_bike.geojson",
            crashes: "data/cambridge/crashes_rollup_bike.geojson"
        },
        {
            id: "cambridge_pedestrian",
            name: "Cambridge, Massachusetts, USA (pedestrian)",
            latitude: 42.3736158,
            longitude: -71.10973349999999,
            speed_unit: "mph",
            file: "data/cambridge/preds_viz_pedestrian.geojson",
            crashes: "data/cambridge/crashes_rollup_pedestrian.geojson"
        },
        {
            id: "cambridge_vehicle",
            name: "Cambridge, Massachusetts, USA (vehicle)",
            latitude: 42.3736158,
            longitude: -71.10973349999999,
            speed_unit: "mph",
            file: "data/cambridge/preds_viz_vehicle.geojson",
            crashes: "data/cambridge/crashes_rollup_vehicle.geojson"
        },
        {
            name: "Somerville, Massachusetts, USA (pedestrian)",
            id: "somerville_pedestrian",
            latitude: 42.3876,
            longitude: -71.0995,
            speed_unit: "mph",
            file: "data/somerville/preds_viz_pedestrian.geojson",
            crashes: "data/somerville/crashes_rollup_pedestrian.geojson"
        },
        {
            name: "Somerville, Massachusetts, USA (bike)",
            id: "somerville_bike",
            latitude: 42.3876,
            longitude: -71.0995,
            speed_unit: "mph",
            file: "data/somerville/preds_viz_bike.geojson",
            crashes: "data/somerville/crashes_rollup_bike.geojson"
        },
        {
            name: "Somerville, Massachusetts, USA (vehicle)",
            id: "somerville_vehicle",
            latitude: 42.3876,
            longitude: -71.0995,
            speed_unit: "mph",
            file: "data/somerville/preds_viz_vehicle.geojson",
            crashes: "data/somerville/crashes_rollup_vehicle.geojson"
        },
        {
            id: "dc",
            name: "Washington D.C, USA (bike)",
            latitude: 38.9071923,
            longitude: -77.0368707,
            speed_unit: "mph",
            file: "data/dc/preds_viz_bike.geojson",
            crashes: "data/dc/crashes_rollup_bike.geojson"
        },
        {
            id: "dc",
            name: "Washington D.C, USA (pedestrian)",
            latitude: 38.9071923,
            longitude: -77.0368707,
            speed_unit: "mph",
            file: "data/dc/preds_viz_pedestrian.geojson",
            crashes: "data/dc/crashes_rollup_pedestrian.geojson"
        },
        {
            id: "dc",
            name: "Washington D.C, USA (vehicle)",
            latitude: 38.9071923,
            longitude: -77.0368707,
            speed_unit: "mph",
            file: "data/dc/preds_viz_vehicle.geojson",
            crashes: "data/dc/crashes_rollup_vehicle.geojson"
        },
        {
            id: "brisbane",
            name: "Brisbane, Australia (bike)",
            latitude: -27.4697707,
            longitude: 153.0251235,
            speed_unit: "kph",
            file: "data/brisbane/preds_viz_bike.geojson",
            crashes: "data/brisbane/crashes_rollup_bike.geojson"
        },
        {
            id: "brisbane",
            name: "Brisbane, Australia (pedestrian)",
            latitude: -27.4697707,
            longitude: 153.0251235,
            speed_unit: "kph",
            file: "data/brisbane/preds_viz_pedestrian.geojson",
            crashes: "data/brisbane/crashes_rollup_pedestrian.geojson"
        },
        {
            id: "brisbane",
            name: "Brisbane, Australia (vehicle)",
            latitude: -27.4697707,
            longitude: 153.0251235,
            speed_unit: "kph",
            file: "data/brisbane/preds_viz_vehicle.geojson",
            crashes: "data/brisbane/crashes_rollup_vehicle.geojson"
        },
        {
            id: "melbourne",
            name: "Melbourne, Australia (bike)",
            latitude: -37.814,
            longitude: 144.96332,
            speed_unit: "kph",
            file: "data/melbourne/preds_viz_bike.geojson",
            crashes: "data/melbourne/crashes_rollup_bike.geojson"
        },
        {
            id: "melbourne",
            name: "Melbourne, Australia (pedestrian)",
            latitude: -37.814,
            longitude: 144.96332,
            speed_unit: "kph",
            file: "data/melbourne/preds_viz_pedestrian.geojson",
            crashes: "data/melbourne/crashes_rollup_pedestrian.geojson"
        },
        {
            id: "melbourne",
            name: "Melbourne, Australia (vehicle)",
            latitude: -37.814,
            longitude: 144.96332,
            speed_unit: "kph",
            file: "data/melbourne/preds_viz_vehicle.geojson",
            crashes: "data/melbourne/crashes_rollup_vehicle.geojson"
        },
        {
            name: "Ada County (pedestrian)",
            id: "ada_county_pedestrian",
            latitude: 43.60764000000006,
            longitude: -116.19339999999994,
            speed_unit: "mph",
            file: "data/ada_county/preds_viz_pedestrian.geojson",
            crashes: "data/ada_county/crashes_rollup_pedestrian.geojson"
        },
        {
            name: "Ada County (bike)",
            id: "ada_county_bike",
            latitude: 43.60764000000006,
            longitude: -116.19339999999994,
            speed_unit: "mph",
            file: "data/ada_county/preds_viz_bike.geojson",
            crashes: "data/ada_county/crashes_rollup_bike.geojson"
        },
        {
            name: "Ada County (vehicle)",
            id: "ada_county_vehicle",
            latitude: 43.60764000000006,
            longitude: -116.19339999999994,
            speed_unit: "mph",
            file: "data/ada_county/preds_viz_vehicle.geojson",
            crashes: "data/ada_county/crashes_rollup_vehicle.geojson"
        }
]
