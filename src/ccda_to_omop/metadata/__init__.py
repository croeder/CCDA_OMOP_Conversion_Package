

import ccda_to_omop.metadata.person      as person
import ccda_to_omop.metadata.visit_encompassingEncounter_responsibleParty as visit_encompassingEncounter_responsibleParty
import ccda_to_omop.metadata.visit       as visit
import ccda_to_omop.metadata.measurement as measurement
import ccda_to_omop.metadata.measurement_vital_signs as measurement_vs
import ccda_to_omop.metadata.observation as observation
import ccda_to_omop.metadata.observation_social_history_smoking as observation_social_history_smoking
import ccda_to_omop.metadata.observation_social_history_pregnancy as observation_social_history_pregnancy
import ccda_to_omop.metadata.observation_social_history_tobacco_use as observation_social_history_tobacco_use
import ccda_to_omop.metadata.observation_social_history_cultural as observation_social_history_cultural
import ccda_to_omop.metadata.observation_social_history_home_environment as observation_social_history_home_environment
import ccda_to_omop.metadata.condition as condition
import ccda_to_omop.metadata.location as location
import ccda_to_omop.metadata.care_site_ee_hcf_location as care_site_ee_hcf_location
import ccda_to_omop.metadata.care_site_ee_hcf as care_site_ee_hcf
import ccda_to_omop.metadata.care_site_pr_location as care_site_pr_location
import ccda_to_omop.metadata.care_site_pr as care_site_pr
import ccda_to_omop.metadata.provider as provider
import ccda_to_omop.metadata.provider_encompassingEncounter as provider_encompassingEncounter	
import ccda_to_omop.metadata. provider_encompassingEncounter_responsibleParty as provider_encompassingEncounter_responsibleParty
from ccda_to_omop.metadata import visit_encompassingEncounter
import ccda_to_omop.metadata.provider_header_documentationOf as provider_header_documentationOf
import ccda_to_omop.metadata.medication_medication_dispense as medication_medication_dispense
import ccda_to_omop.metadata.medication_medication_activity as medication_medication_activity
import ccda_to_omop.metadata.immunization_immunization_activity as immunization_immunization_activity
import ccda_to_omop.metadata.procedure_activity_procedure as procedure_activity_procedure
import ccda_to_omop.metadata.procedure_activity_observation as procedure_activity_observation
import ccda_to_omop.metadata.procedure_activity_act as procedure_activity_act
import ccda_to_omop.metadata.device_organizer_supply as device_organizer_supply
import ccda_to_omop.metadata.device_supply as device_supply
import ccda_to_omop.metadata.device_organizer_procedure as device_organizer_procedure
import ccda_to_omop.metadata.device_procedure as device_procedure

""" The meatadata is 3 nested dictionaries:
    - meta_dict: the dict of all domains
    - domain_dict: a dict describing a particular domain
    - field_dict: a dict describing a field component of a domain
    These names are used in the code to help orient the reader

    An output_dict is created for each domain. The keys are the field names,
    and the values are the values of the attributes from the elements.

    REMEMBER to update the ddl.py file as well.
"""

# ***
#  NB: *** Order is important here. ***
# ***
#  PKs like person and visit must come before referencing FK configs, like in measurement

meta_dict =  location.metadata | \
             provider_header_documentationOf.metadata | \
             person.metadata | \
             visit_encompassingEncounter.metadata | \
             visit_encompassingEncounter_responsibleParty.metadata | \
             visit.metadata  | \
             measurement.metadata | \
             measurement_vs.metadata | \
             observation.metadata  | \
             observation_social_history_smoking.metadata | \
             observation_social_history_pregnancy.metadata | \
             observation_social_history_tobacco_use.metadata | \
             observation_social_history_cultural.metadata | \
             observation_social_history_home_environment.metadata | \
             medication_medication_dispense.metadata | \
             medication_medication_activity.metadata | \
             condition.metadata | \
             care_site_ee_hcf.metadata | \
             care_site_ee_hcf_location.metadata | \
             care_site_pr.metadata | \
             care_site_pr_location.metadata | \
             provider.metadata | \
             immunization_immunization_activity.metadata | \
             procedure_activity_procedure.metadata | \
             procedure_activity_observation.metadata | \
             procedure_activity_act.metadata | \
             device_organizer_supply.metadata | \
             device_supply.metadata | \
             device_organizer_procedure.metadata | \
             device_procedure.metadata | \
             provider_encompassingEncounter.metadata | \
             provider_encompassingEncounter_responsibleParty.metadata 


def get_meta_dict():
    return meta_dict
