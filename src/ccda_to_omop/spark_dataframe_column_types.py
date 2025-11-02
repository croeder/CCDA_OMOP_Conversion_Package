import datetime
from numpy import datetime64
from numpy import float32
from numpy import int32  # int
from numpy import int64  # long
from pyspark.sql.types import StructType, StructField
from pyspark.sql.types import IntegerType, StringType, LongType, FloatType
from pyspark.sql.types import TimestampType, DateType

# Spark data types to impose them when creating a dataframe
# rather than having it infer from the data.

spark_dataframe_column_types = {
    # table names here
    "care_site": StructType([
        StructField("care_site_id", IntegerType(), True),
        StructField("care_site_name", StringType(), True),
        StructField("place_of_service_concept_id", LongType(), True), # int32
        StructField("location_id", IntegerType(), True),
        StructField("care_site_source_value", StringType(), True),
        StructField("place_of_service_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "location": StructType([
        StructField("location_id", IntegerType(), True),
        StructField("address_1", StringType(), True),
        StructField("address_2", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zip", StringType(), True),
        StructField("county", StringType(), True),
        StructField("location_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "provider": StructType([
        StructField("provider_id", IntegerType(), True),
        StructField("provider_name", StringType(), True),
        StructField("npi", StringType(), True),
        StructField("dea", StringType(), True),
        StructField("specialty_concept_id", LongType(), True), # int32
        StructField("care_site_id", IntegerType(), True),
        StructField("year_of_birth", LongType(), True), # int32
        StructField("gender_concept_id", LongType(), True), # int32
        StructField("provider_source_value", StringType(), True),
        StructField("specialty_source_value", StringType(), True),
        StructField("specialty_source_concept_id", LongType(), True), # int32
        StructField("gender_source_value", StringType(), True),
        StructField("gender_source_concept_id", LongType(), True), # int32
        StructField("filename", StringType(), True),
    ]),
    "person": StructType([
        StructField("person_id", IntegerType(), True),
        StructField("gender_concept_id", LongType(), True), # int32
        StructField("year_of_birth", LongType(), True), # int32
        StructField("month_of_birth", LongType(), True), # int32
        StructField("day_of_birth", LongType(), True), # int32
        StructField("birth_datetime", TimestampType(), True),
        StructField("race_concept_id", LongType(), True), # int32
        StructField("ethnicity_concept_id", LongType(), True), # int32
        StructField("location_id", IntegerType(), True),
        StructField("provider_id", IntegerType(), True),
        StructField("care_site_id", IntegerType(), True),
        StructField("person_source_value", StringType(), True),
        StructField("gender_source_value", StringType(), True),
        StructField("gender_source_concept_id", LongType(), True), # int32
        StructField("race_source_value", StringType(), True),
        StructField("race_source_concept_id", LongType(), True), # int32
        StructField("ethnicity_source_value", StringType(), True),
        StructField("ethnicity_source_concept_id", LongType(), True), # int32
        StructField("filename", StringType(), True),
    ]),
    "visit_occurrence": StructType([
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("person_id", IntegerType(), True),
        StructField("visit_concept_id", LongType(), True), # int32
        StructField("visit_start_date", DateType(), True),
        StructField("visit_start_datetime", TimestampType(), True),
        StructField("visit_end_date", DateType(), True),
        StructField("visit_end_datetime", TimestampType(), True),
        StructField("visit_type_concept_id", LongType(), True), # int32
        StructField("provider_id", IntegerType(), True),
        StructField("care_site_id", IntegerType(), True),
        StructField("visit_source_value", StringType(), True),
        StructField("visit_source_concept_id", LongType(), True), # int32
        StructField("admitting_source_value", StringType(), True),
        StructField("admitting_source_concept_id", LongType(), True), # int32
        StructField("discharge_to_concept_id", LongType(), True), # int32
        StructField("discharge_to_source_value", StringType(), True),
        StructField("preceding_visit_occurrence_id", IntegerType(), True),
        StructField("filename", StringType(), True),
    ]),
    "measurement": StructType([
        StructField("measurement_id", IntegerType(), True),
        StructField("person_id", IntegerType(), True),
        StructField("measurement_concept_id", LongType(), True), # int32
        StructField("measurement_date", DateType(), True),
        StructField("measurement_datetime", TimestampType(), True),
        StructField("measurement_time", StringType(), True),
        StructField("measurement_type_concept_id", LongType(), True), # int32
        StructField("operator_concept_id", LongType(), True), # int32
        StructField("value_as_number", FloatType(), True), # float32
        StructField("value_as_concept_id", LongType(), True), # int32
        StructField("unit_concept_id", LongType(), True), # int32
        StructField("range_low", FloatType(), True), # float32
        StructField("range_high", FloatType(), True), # float32
        StructField("provider_id", IntegerType(), True),
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("visit_detail_id", IntegerType(), True),
        StructField("measurement_source_value", StringType(), True),
        StructField("measurement_source_concept_id", LongType(), True), # int32
        StructField("unit_source_value", StringType(), True),
        StructField("value_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "observation": StructType([
        StructField("observation_id", IntegerType(), True),
        StructField("person_id", IntegerType(), True),
        StructField("observation_concept_id", LongType(), True), # int32
        StructField("observation_date", DateType(), True),
        StructField("observation_datetime", TimestampType(), True),
        StructField("observation_type_concept_id", LongType(), True), # int32
        StructField("value_as_number", FloatType(), True), # float32
        StructField("value_as_string", StringType(), True),
        StructField("value_as_concept_id", LongType(), True), # int32
        StructField("qualifier_concept_id", LongType(), True), # int32
        StructField("unit_concept_id", LongType(), True), # int32
        StructField("provider_id", IntegerType(), True),
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("visit_detail_id", IntegerType(), True),
        StructField("observation_source_value", StringType(), True),
        StructField("observation_source_concept_id", LongType(), True), # int32
        StructField("unit_source_value", StringType(), True),
        StructField("qualifier_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "condition_occurrence": StructType([
        StructField("condition_occurrence_id", IntegerType(), True),
        StructField("person_id", IntegerType(), True),
        StructField("condition_concept_id", LongType(), True), # int32
        StructField("condition_start_date", DateType(), True),
        StructField("condition_start_datetime", TimestampType(), True),
        StructField("condition_end_date", DateType(), True),
        StructField("condition_end_datetime", TimestampType(), True),
        StructField("condition_type_concept_id", LongType(), True), # int32
        StructField("condition_status_concept_id", LongType(), True), # int32
        StructField("stop_reason", StringType(), True),
        StructField("provider_id", IntegerType(), True),
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("visit_detail_id", IntegerType(), True),
        StructField("condition_source_value", StringType(), True),
        StructField("condition_source_concept_id", LongType(), True), # int32
        StructField("condition_status_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "procedure_occurrence": StructType([
        StructField("procedure_occurrence_id", IntegerType(), True),
        StructField("person_id", IntegerType(), True),
        StructField("procedure_concept_id", LongType(), True), # int32
        StructField("procedure_date", DateType(), True),
        StructField("procedure_datetime", TimestampType(), True),
        StructField("procedure_type_concept_id", LongType(), True), # int32
        StructField("modifier_concept_id", LongType(), True), # int32
        StructField("quantity", LongType(), True), # int32
        StructField("provider_id", IntegerType(), True),
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("visit_detail_id", IntegerType(), True),
        StructField("procedure_source_value", StringType(), True),
        StructField("procedure_source_concept_id", LongType(), True), # int32
        StructField("modifier_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "drug_exposure": StructType([
        StructField("drug_exposure_id", IntegerType(), True),
        StructField("person_id", IntegerType(), True),
        StructField("drug_concept_id", LongType(), True), # int32
        StructField("drug_exposure_start_date", DateType(), True),
        StructField("drug_exposure_start_datetime", TimestampType(), True),
        StructField("drug_exposure_end_date", DateType(), True),
        StructField("drug_exposure_end_datetime", TimestampType(), True),
        StructField("verbatim_end_date", DateType(), True),
        StructField("drug_type_concept_id", LongType(), True), # int32
        StructField("stop_reason", StringType(), True),
        StructField("refills", LongType(), True), # int32
        StructField("quantity", FloatType(), True), # float32
        StructField("days_supply", LongType(), True), # int32
        StructField("sig", StringType(), True),
        StructField("route_concept_id", LongType(), True), # int32
        StructField("lot_number", StringType(), True),
        StructField("provider_id", IntegerType(), True),
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("visit_detail_id", IntegerType(), True),
        StructField("drug_source_value", StringType(), True),
        StructField("drug_source_concept_id", LongType(), True), # int32
        StructField("route_source_value", StringType(), True),
        StructField("dose_unit_source_value", StringType(), True),
        StructField("filename", StringType(), True),
    ]),
    "device_exposure": StructType([
        StructField("device_exposure_id", LongType(), True), # int32
        StructField("person_id", IntegerType(), True),
        StructField("device_concept_id", LongType(), True), # int32
        StructField("device_exposure_start_date", DateType(), True),
        StructField("device_exposure_start_datetime", TimestampType(), True),
        StructField("device_exposure_end_date", DateType(), True),
        StructField("device_exposure_end_datetime", TimestampType(), True),
        StructField("device_type_concept_id", LongType(), True), # int32
        StructField("unique_device_id", StringType(), True),
        StructField("quantity", LongType(), True), # int32
        StructField("provider_id", IntegerType(), True),
        StructField("visit_occurrence_id", IntegerType(), True),
        StructField("visit_detail_id", IntegerType(), True),
        StructField("device_source_value", StringType(), True),
        StructField("device_source_concept_id", LongType(), True), # int32
    ]),
}
