import datetime
import json
import logging
import os.path
import platform
import shutil
import xmltodict

from portada_data_layer.boat_fact_model import BoatFactDataModel
from portada_data_layer.data_lake_metadata_manager import DataLakeMetadataManager
from portada_data_layer import DeltaDataLayerBuilder, PortadaBuilder
from portada_data_layer.portada_cleaning import PortadaCleaning

import sys
print(sys.executable)   # ruta de l'intèrpret que s'està usant
print(sys.path)         # rutes on busca mòdul
print(xmltodict.__file__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("delta_data_layer")
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    so = platform.system()
    if so == "Darwin":
        base_path = "/Users/josepcanellas/Dropbox/feinesJordi/implementacio/delta_lake/delta_test"
        json_path_to_copy = "/Users/josepcanellas/Dropbox/feinesJordi/dades/resultats/prova"
        copy_path = "/Users/josepcanellas/tmp/json_data"
        path_to_copy = "/Users/josepcanellas/tmp"
        schema_path = "/Users/josepcanellas/Dropbox/feinesJordi/github/delta_data_layer_config/config/schema.json"
        regex_mapping_path = "/Users/josepcanellas/Dropbox/feinesJordi/github/delta_data_layer_config/config/mapping_to_clean_chars.json"
        config_path = "/Users/josepcanellas/Dropbox/feinesJordi/github/delta_data_layer_config/config/delta_data_layer_config.json"

    else:
        base_path = "/home/josep/Dropbox/feinesJordi/implementacio/delta_lake/delta_test"
        json_path_to_copy = "/home/josep/Dropbox/feinesJordi/dades/resultats/prova"
        copy_path = "/home/josep/tmp/json_data"
        path_to_copy = "/home/josep/tmp"
        schema_path = "/home/josep/Dropbox/feinesJordi/github/delta_data_layer_config/config/schema.json"
        regex_mapping_path = "/home/josep/Dropbox/feinesJordi/github/delta_data_layer_config/config/mapping_to_clean_chars.json"
        config_path = "/home/josep/Dropbox/feinesJordi/github/delta_data_layer_config/config/delta_data_layer_config.json"

    user = "jcanell4"

    data_path = "dummy_data"
    builder = (
        DeltaDataLayerBuilder()
        .protocol("file://")
        .base_path(base_path)
        .app_name("DeltaLakeExample")
        .config("spark.sql.shuffle.partitions", "1")
    )
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    layer = builder.build()
    layer.verbose = True
    layer.start_session()
    # print("--------config_dict--------")
    # print(f"{type(layer)}:{layer.__dict__}")
    # print("-----------------------")
    df = layer.spark.createDataFrame([(1, "Vaixell A"), (2, "Vaixell B")], ["id", "nom"])
    df = layer.write_delta(data_path, "vaixells", df=df)
    df = layer.write_delta((data_path, "vaixells2"), df=df)
    df = layer.write_delta(f"{data_path}/vaixells3", df=df)

    df2_0 = layer.read_delta(data_path, "vaixells")
    df2_1 = layer.read_delta((data_path, "vaixells"))
    df2_2 = layer.read_delta(f"{data_path}/vaixells")

    if df2_0.subtract(df2_1).count() == 0:
        print("Ok for df2_0 and df2_1")
    else:
        print("KO for df2_0 and df2_1")

    if df2_0.subtract(df2_2).count() == 0:
        print("Ok for df2_0 and df2_2")
    else:
        print("KO for df2_0 and df2_2")

    layer.register_temp_table(df2_0, "vaixells")
    result = layer.sql("SELECT COUNT(*) AS total FROM vaixells")
    result.show()

    # layer.stop_session()

    with open(config_path) as f:
        config = json.load(f)

    builder = (
        PortadaBuilder(config)
        .protocol("file://")
        .base_path(base_path)
        .app_name("DeltaLakeExample")
        .project_name("default_portada")
        .config("spark.sql.shuffle.partitions", "4")
    )

    json_name = "results_boatdata.extractor.json"
    os.makedirs(copy_path, exist_ok=True)
    shutil.copy(os.path.join(json_path_to_copy, json_name), os.path.join(copy_path, json_name))
    json_path = os.path.join(copy_path, json_name)
    data_path = "ship_entries"
    layer = builder.build(builder.NEWS_TYPE)
    # print("--------config_dict--------")
    # print(f"{type(layer)}:{layer.__dict__}")
    # print("-----------------------")
    layer.start_session()
    layer.ingest(data_path, user=user, local_path=json_path)
    df = layer.read_raw_data(data_path, user=user, publication_name="DB", d="2[0-5]")
    print(f"Entrades: {df.count()}")
    print("............................................................")
    print("---------------------------SCHEMA---------------------------")
    print(df.printSchema())
    print("............................................................")
    c = 0
    lc = []
    for d in range(20, 26, 1):
        df = layer.read_raw_data(data_path, publication_name="DB", d=d)
        lc.append(0 if df is None else df.count())
        c += lc[d - 20]
    print(f"Entrades: {lc[0]} + {lc[1]} + {lc[2]} + {lc[3]} + {lc[4]} + {lc[5]} = {c}")
    data2 = []
    with open(os.path.join(json_path_to_copy, json_name)) as json_data:
        data = json.load(json_data)
    for js in data:
        b_json = BoatFactDataModel(js)
        ts = datetime.datetime.fromtimestamp(int(b_json["publication_date"]) / 1000)
        if 20 <= ts.day <= 25:
            data2.append(js)
    layer.save_raw_data(data_path, data=data2, user=user)
    df = layer.read_raw_data(data_path, publication_name="DB", d="2[0-5]")
    print(f"Entrades: {df.count()}")

    metadata = DataLakeMetadataManager(layer.get_configuration())
    # df_meta = metadata.read_all_logs(["storage_log", "process_log"])

    df_meta = metadata.read_log("process_log")

    df_meta.filter("process = 'ingest.save_raw_data'").show(n=100)
    df_meta.filter("process = 'ingest.copy_ingested_raw_data'").show(n=100)
    df_meta.filter(df_meta.process.rlike("save_raw_data$")).show(n=100)
    df_meta.filter(df_meta.process.rlike("copy_ingested_raw_data$")).show(n=100)
    df_meta.show(n=100)

    df_dup = metadata.read_log("duplicates_log")
    df_dup.filter("lower(publication)='db'").show(n=100)
    df_dup_1850_01_22 = df_dup.filter("lower(publication)='db' AND date == '1850-01-22'").first()
    duplicates = metadata.read_log("duplicates_records")
    duplicates.filter(df_dup_1850_01_22.duplicates_filter).filter(duplicates.entry_id.isin(df_dup_1850_01_22.duplicate_ids)).show(n=100)

    print("------------------DUPLICATES SCHEMA------------------------")
    print(duplicates.printSchema())

    df_meta_storage = metadata.read_log("storage_log")
    df_meta_storage.show(n=100)

    df_meta_lineage = metadata.read_log("field_lineage_log")

    rows = df_meta_storage.take(5)
    print("LINEAGE------------------------")
    for row in rows:
        rows2 = df_meta_lineage.filter(df_meta_lineage.stored_log_id==row.log_id).collect()
        print(f"Lineage for storage id: {row.log_id}")
        for row2 in rows2:
            print(f"transformer_name: {row2.transformer_name}")
            print(f"dataframe_name: {row2.dataframe_name}")
            print(f"action: {row2.change_action}({row2.arguments})")
            print(f"involved_columns: {','.join(row2.involved_columns)}")
        print("---------------")



    missing_date_list = layer.get_missing_dates_from_a_newspaper(data_path, publication_name="db")

    print(missing_date_list)

    missing_date_list = layer.get_missing_dates_from_a_newspaper(data_path, publication_name="db", start_date="1850-01-26")

    print(missing_date_list)

    missing_date_list = layer.get_missing_dates_from_a_newspaper(data_path, publication_name="db", start_date="1850-01-26", end_date="1850-02-03")

    print(missing_date_list)

    df = layer.read_raw_data(data_path)

    # layer.stop_session()

    file_name = "prova_portada.txt"
    shutil.copy(os.path.join(path_to_copy, file_name), os.path.join(copy_path, file_name))

    layer = builder.build(builder.KNOWN_ENTITIES_TYPE)
    layer.start_session()
    # print("--------config_dict--------")
    # print(f"{type(layer)}:{layer.__dict__}")
    # print("-----------------------")
    data, dest = layer.copy_ingested_entities(entity="pr", local_path=f"{os.path.join(copy_path, file_name)}",
                                          return_dest_path=True)
    odata = {"source_path": dest, "data": data}
    layer.save_raw_entities(entity="pr", data=odata)
    df_entity_pr = layer.read_raw_entities(entity="pr")
    df_entity_pr.show(n=100)

    # layer.stop_session()

    layer : PortadaCleaning = builder.build(PortadaCleaning.__name__)

    with open(schema_path) as f:
        schema = json.load(f)

    with open(regex_mapping_path) as f:
        regex_mapping = json.load(f)

    layer.start_session()
    # print("--------config_dict--------")
    # print(f"{type(layer)}:{layer.__dict__}")
    # print("-----------------------")

    df.select("travel_port_of_call_list").show(n=100, truncate=False)

    df = layer.use_schema(schema).use_mapping_to_clean_chars(regex_mapping).cleaning(df)

    # layer.save_original_values_of_ship_entries(df)
    #
    # with open(schema_path) as f:
    #     schema = json.load(f)
    #
    # df = layer.use_schema(schema).prune_unaccepted_fields(df)

    for c in df.columns:
        print(c)

    print(df.printSchema())

    df.select("travel_port_of_call_list").show(n=100, truncate=False)

    df.show(n=100)
    df_DB_109 = df.filter(df.entry_id=="DB_109")

    rows = df_DB_109.take(5)
    print("COMPARE_CLEANING------------------------")
    for row in rows:
        for field in schema.get("properties", {}):
            print(f"{field}: {row[field]}")
        print("----------------------------------------")

    layer.stop_session()
