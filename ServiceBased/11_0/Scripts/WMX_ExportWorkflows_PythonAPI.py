# Name:        Export Workflow Manager diagrams and job templates using the ArcGIS Python API
#
# Purpose:      This tool performs the following functions:
#               - Exports diagram and job template configurations from the workflow item into individual JSON files
#
# Author:      Tiffany Weintraub (tweintraub@esri.com) and Mark Torrey (mtorrey@esri.com); William Rene Moreno (wmoreno@esri.co)
# Created:     11/4/2021
# Updated:     17/05/2023
# 
# COPYRIGHT © 2022 Esri
# All material copyright ESRI, All Rights Reserved, unless otherwise specified.
# See https://github.com/Esri/workflowmanager-samples/blob/master/License.txt for details.
 
##-----------------------------------------------------------------------------------------------
# ------------------------------------------ Modules ------------------------------------------------------
import arcpy, os, json
from arcgis.gis import GIS
from arcgis.gis.workflowmanager import WorkflowManager
from arcgis.geoprocessing._tool import _camelCase_to_underscore
import Config

#
portal = GIS(
    url=Config.portal_params.portal_url,
    password=Config.portal_params.p_password,
    username=Config.portal_params.p_username,
)
arcpy.AddMessage(f"\t--> connected as {portal.properties.user.username} to {portal.url}")
# Get workflow items in the source and destination environments

#------------------------------------------ Parameters ---------------------------------------------------------
source_wfm_itemID = arcpy.GetParameterAsText(0)
json_dir = arcpy.GetParameterAsText(1)
source_wf_item = portal.content.get(source_wfm_itemID)
source_wm = WorkflowManager(source_wf_item)

# #--------------------------------------------- Main ------------------------------------------------------------
def exportDiagrams(diagrams_ids=[]):
    try: 
        arcpy.AddMessage(f'\nGetting workflow items from source Portal...')

        arcpy.AddMessage(f'\nExporting configuration files...')
        if not os.path.exists(json_dir):
            os.mkdir(json_dir)
                
        diagram_ids = [x.diagram_id for x in source_wm.diagrams]
        for id in diagram_ids:
            d = source_wm.diagram(id)
            file_path = os.path.join(json_dir, f"Diagram___{d.diagram_id}.json")
            with open(file_path, 'w') as file:
                s = {
                "diagram_name": d.diagram_name, 
                "steps": d.steps, 
                "display_grid": d.display_grid, 
                "description": d.description,
                "active": True,
                "diagram_version": d.diagram_version, 
                "annotations": d.annotations, 
                "data_sources": d.data_sources,
                "diagram_id": d.diagram_id,
                "initial_step_id": d.initial_step_id,
                "initial_step_name": d.initial_step_name
                }
                json.dump(s, file)

            arcpy.AddMessage(f'\t...Created diagram {d.diagram_name} JSON file.')

        arcpy.AddMessage(f'\n\n')

        arcpy.AddMessage(f'\n\nDiagrams exported successfully!')

    except Exception as ex:
        arcpy.AddMessage(str(ex))


def exportJobTemplates(job_templates_ids=[]):
    try: 
        arcpy.AddMessage(f'\nGetting workflow items from source Portal...')

        arcpy.AddMessage(f'\nExporting job_templates files...')
        if not os.path.exists(json_dir):
            os.mkdir(json_dir)
        
        template_ids = [x.job_template_id for x in source_wm.job_templates]
        for t_id in template_ids:
            j = source_wm.job_template(t_id)
            template_file_path = os.path.join(json_dir, f"Template___{t_id}.json")
            with open(template_file_path, 'w') as t_file:
                t = {
                    "name": j.job_template_name, 
                    "priority": j.default_priority_name,
                    "id": j.job_template_id,
                    "assigned_to": j.default_assigned_to,
                    "diagram_id": j.diagram_id, 
                    "diagram_name": j.diagram_name,
                    "assigned_type": j.default_assigned_type, 
                    "description": j.description, 
                    "state": j.state, 
                    "extended_property_table_definitions": j.extended_property_table_definitions
                }
                json.dump(t, t_file)

            arcpy.AddMessage(f'\t...Created job template {j.job_template_name} JSON. ')

        arcpy.AddMessage(f'\n\nConfiguration files exported successfully!')

    except Exception as ex:
        arcpy.AddMessage(str(ex))


# Inicio Extender clases del api de Python:
class WorkflowManagerSgc(WorkflowManager):
    def __init__(self, item):
        """initializer"""
        super().__init__(item)
    
    @property
    def email_templates(self):
        """
        Gets all the email templates in a workflow item.
        :return:
            List of all current :class:`email templates <arcgis.gis.workflowmanager.EmailTemplate>`
            in the Workflow Manager (required information for create_email call).
        """
        try:
            a = self._gis._con.get(
                "{base}/templates/email".format(base=self._url),
                params={"token": self._gis._con.token},
            )["templates"]
            b = json.dumps(a)
            c = json.loads(b)
            template_array = json.loads(
                json.dumps(
                    self._gis._con.get(
                        "{base}/templates/email".format(base=self._url),
                        params={"token": self._gis._con.token},
                    )["templates"]
                )
            )
            # return template_array
            return_array = [
                EmailTemplate(t, self._gis, self._url) for t in template_array
            ]
            return return_array
        except:
            self._handle_error(sys.exc_info())

    def email_template(self, id):
        """
        Returns a email template with the given ID

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        id                  Required string. Job Template ID
        ===============     ====================================================================

        :return:
            Workflow Manager :class:`EmailTemplate <arcgis.gis.workflowmanager.EmailTemplate>` Object

        """
        try:
            return EmailTemplate.get(
                self._gis,
                "{base}/templates/email/{emailTemplate}".format(
                    base=self._url, emailTemplate=id
                ),
                {"token": self._gis._con.token},
            )
        except:
            self._handle_error(sys.exc_info())


def _underscore_to_camelcase(name):
    def camelcase():
        yield str.lower
        while True:
            yield str.capitalize

    c = camelcase()
    return "".join(next(c)(x) if x else "_" for x in name.split("_"))


class EmailTemplate(object):
    """
    Represents a Workflow Manager Email Template object with accompanying GET, POST, and DELETE methods
    ===============     ====================================================================
    **Argument**        **Description**
    ---------------     --------------------------------------------------------------------
    init_data           data object representing relevant parameters for GET or POST calls
    ===============     ====================================================================
    """
    _camelCase_to_underscore = _camelCase_to_underscore
    _underscore_to_camelcase = _underscore_to_camelcase

    def __init__(self, init_data, gis=None, url=None):
        for key in init_data:
            setattr(self, _camelCase_to_underscore(key), init_data[key])
        self._gis = gis
        self._url = url

    def __getattr__(self, item):
        possible_fields = [
            "email_template_name",
            "email_template_id"
        ]
        gis = object.__getattribute__(self, "_gis")
        url = object.__getattribute__(self, "_url")
        id = object.__getattribute__(self, "email_template_id")
        full_object = json.loads(
            json.dumps(gis._con.get(url, {"token": gis._con.token}))
        )
        try:
            setattr(self, _camelCase_to_underscore(item), full_object[item])
            return full_object[item]
        except KeyError:
            if item in possible_fields:
                setattr(self, _camelCase_to_underscore(item), None)
                return None
            else:
                raise KeyError(f'The attribute "{item}" is invalid for Email Templates')

    def get(gis, url, params):
        email_template_dict = json.loads(json.dumps(gis._con.get(url, params)))
        return EmailTemplate(email_template_dict, gis, url)


def ejecutarServicioWfm(urlWfmService, bodyParams=None, post_get="post"):
    thetoken = gis._con.token
    urlWfmService += thetoken
    addMessage("urlWfmService:{}; bodyParams:{}".format(urlWfmService, bodyParams))
    if bodyParams:
        r = requests.post(url=urlWfmService, data=bodyParams)
    else:
        if post_get == "get":
            r = requests.get(url=urlWfmService)
        else:
            r = requests.post(url=urlWfmService)
    resultService = json.loads(r.text)
    addMessage(resultService)
    return resultService
# Fin Extender clases del api de Python


def exportEmailNotifications():
    arcpy.AddMessage(f'\nGetting workflow Email Notifications from source Portal...')
    arcpy.AddMessage(f'\nExporting configuration files...')
    if not os.path.exists(json_dir):
        os.mkdir(json_dir)
            
    # Email Notifications:
    _settings = source_wm.settings
    file_path = os.path.join(json_dir, f"settings___EmailNotifications.json")
    with open(file_path, 'w') as file:
        x = { "settings":_settings }
        json.dump(x, file)
    arcpy.AddMessage(f'\t...Created Email Notifications JSON file. Update email PASSWORD please')

    source_wm_sgc = WorkflowManagerSgc(source_wf_item)
    template_ids = [x.template_id for x in source_wm_sgc.email_templates]
    
    # # 1 notification template * 1 File :
    # for t_id in template_ids:
    #     j = source_wm_sgc.email_template(t_id)
    #     template_file_path = os.path.join(json_dir, f"EmailTemplate___{t_id}.json")
    #     with open(template_file_path, 'w') as t_file:
    #         t = {
    #             "templateName": j.template_name, 
    #             "templateDetails": j.template_details
    #         }
    #         json.dump(t, t_file)
    #     arcpy.AddMessage(f'\t...Created Email template {j.template_name} JSON. ')
    
    # All notifications in one file:
    email_templates = []
    for t_id in template_ids:
        j = source_wm_sgc.email_template(t_id)
        t = {
            "templateName": j.template_name, 
            "templateDetails": j.template_details
        }
        email_templates.append(t)
    template_file_path = os.path.join(json_dir, "EmailTemplate___ALL.json")
    with open(template_file_path, 'w') as t_file:
        json.dump(email_templates, t_file)

    arcpy.AddMessage(f'\t...Created Email Template JSON file.')


def exportLookupStatus():
    arcpy.AddMessage(f'\nGetting workflow Lookup status from source Portal...')
    source_wf_item = portal.content.get(source_wfm_itemID)
    source_wm = WorkflowManager(source_wf_item)
    arcpy.AddMessage(f'\nExporting lookups status file...')
    if not os.path.exists(json_dir):
        os.mkdir(json_dir)
    
    _lookups = source_wm.lookups("status")
    file_path = os.path.join(json_dir, f"lookups___status.json")
    with open(file_path, 'w') as file:
        x = {
            "lookups":_lookups.lookups
        }
        json.dump(x, file)
    arcpy.AddMessage(f'\t...Created status JSON file.')


def exportConfiguration():
    exportDiagrams()
    exportJobTemplates()
    exportEmailNotifications()
    exportLookupStatus()


if __name__ == '__main__':
    exportConfiguration()