# Name:        Import Workflow Manager diagrams and job templates using the ArcGIS Python API
#
# Purpose:      This tool performs the following functions:
#               - Creates two lists: a) diagram files  b) template files
#               - Creates the missing diagrams destination workflow instance. Creates a dictionary of original and new diagram id's
#               - Creats the missing job templates in the destination workflow instance. Extended property tables are created as well so long 
#                   as there is not a table with the same name that exists in the service already.
#
# Author:      Tiffany Weintraub (tweintraub@esri.com) and Mark Torrey (mtorrey@esri.com); William Rene Moreno (wmoreno@esri.co)
# Created:     11/4/2021
# Updated:     17/05/2023
#
# COPYRIGHT © 2022 Esri
# All material copyright ESRI, All Rights Reserved, unless otherwise specified.
# See https://github.com/Esri/workflowmanager-samples/blob/master/License.txt for details.
#
##---------------------------------------------------------------------------------------------------------
import arcpy, os, json
from arcgis.gis import GIS
from arcgis.gis.workflowmanager import WorkflowManager
from arcgis.geoprocessing._tool import _camelCase_to_underscore
import Config

#
portal = GIS(
    url=Config.dest_portal_params.portal_url,
    password=Config.dest_portal_params.p_password,
    username=Config.dest_portal_params.p_username,
)
arcpy.AddMessage(f"\t--> connected as {portal.properties.user.username} to {portal.url}")
# Get workflow items in the source and destination environments

#------------------------------------------ Parameters ----------------------------------------------------
dest_wfm_itemID = arcpy.GetParameterAsText(0)
folder = arcpy.GetParameterAsText(1)
dest_wf_item = portal.content.get(dest_wfm_itemID)
dest_wm = WorkflowManager(dest_wf_item)

# #--------------------------------------------- Main -----------------------------------------------------
def importDiagrams():
    try:
        arcpy.AddMessage(f'\nGetting workflow items from destination Portal...')
        table_defs = [t['tableName'] for t in dest_wm.table_definitions]

        # Create a list of diagram files and a list of job template files
        wmx_files = os.listdir(folder)
        diagram_files = []
        template_files = []

        for f in wmx_files:
            if "Template_" in f:
                template_files.append(os.path.join(folder, f))
            else:
                diagram_files.append(os.path.join(folder, f))

        # Import diagrams
        arcpy.AddMessage(f'\nImporting diagrams into workflow item...')
        diagram_id_map = {}
        existing_diagrams = [x.diagram_name for x in dest_wm.diagrams]
        for df in diagram_files:
            with open(df, 'r') as w:
                d = json.load(w)
                d_name = d['diagram_name']

                if d_name not in existing_diagrams:
                    arcpy.AddMessage(f'\tImporting {d_name} diagram...')
                    orig_id = d['diagram_id']
                    new_id = dest_wm.create_diagram(
                        name=d['diagram_name'], 
                        steps=d['steps'], 
                        display_grid=d['display_grid'], 
                        description=d['description'], 
                        active=d['active'],
                        annotations=d['annotations'], 
                        data_sources=d['data_sources'],
                        )

                    arcpy.AddMessage(f'\t\t{d_name} diagram imported successfully! New Diagram ID = {new_id}')
                    diagram_id_map.update({orig_id: new_id})
                else:
                    arcpy.AddMessage(f'\t...{d_name} diagram already exists in destination workflow item')
                    filename = os.path.basename(df).split('___')[1]
                    orig_id = filename[:-5]
                    new_id = [x.diagram_id for x in dest_wm.diagrams if x.diagram_name == d_name][0]
                    diagram_id_map.update({orig_id: new_id})
    except Exception as ex:
        arcpy.AddMessage(str(ex))


def importJobTemplates():
    # Import job templates
    try:
        arcpy.AddMessage(f'\n\n')
        # Create a list of diagram files and a list of job template files
        wmx_files = os.listdir(folder)
        template_files = []
        for f in wmx_files:
            if "Template_" in f:
                template_files.append(os.path.join(folder, f))
        
        existing_templates = [x.job_template_name for x in dest_wm.job_templates]
        for jt in template_files:
            with open(jt, 'r') as x:
                j = json.load(x)
                source_diagram_id = j['diagram_id']
                new_diagram_id = diagram_id_map.get(source_diagram_id)
                template_name = j['name']

                if template_name not in existing_templates:
                    arcpy.AddMessage(f'\tImporting {template_name} job template...')
                    existing_defs = j['extended_property_table_definitions']
                    if existing_defs:
                        tnames = [t['tableName'] for t in j['extended_property_table_definitions']]
                        for t in tnames:
                            if t not in table_defs: 
                                new_template_id = dest_wm.create_job_template(
                                    name=j['name'], 
                                    priority=j['priority'],
                                    id=j['id'],
                                    assigned_to=j['assigned_to'],
                                    diagram_id=new_diagram_id, 
                                    diagram_name=j['diagram_name'],
                                    assigned_type=j['assigned_type'], 
                                    description=j['description'], 
                                    state=j['state'], 
                                    extended_property_table_definitions=j['extended_property_table_definitions']
                                    )
                                
                                arcpy.AddMessage(f'\t\t{template_name} job template imported successfully with extended properties table(s)')
                            else:
                                new_template_id = dest_wm.create_job_template(
                                    name=j['name'], 
                                    priority=j['priority'],
                                    id=j['id'],
                                    assigned_to=j['assigned_to'],
                                    diagram_id=new_diagram_id, 
                                    diagram_name=j['diagram_name'],
                                    assigned_type=j['assigned_type'], 
                                    description=j['description'], 
                                    state=j['state']
                                    )

                                arcpy.AddMessage(f'\t\t{template_name} imported successfully without extended properties table(s)')
                    else:
                        new_template_id = dest_wm.create_job_template(
                                    name=j['name'], 
                                    priority=j['priority'],
                                    id=j['id'],
                                    assigned_to=j['assigned_to'],
                                    diagram_id=new_diagram_id, 
                                    diagram_name=j['diagram_name'],
                                    assigned_type=j['assigned_type'], 
                                    description=j['description'], 
                                    state=j['state'], 
                                    extended_property_table_definitions=j['extended_property_table_definitions']
                                    )
                                
                        arcpy.AddMessage(f'\t...{template_name} job template imported successfully with extended properties table(s)')
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


def importEmailNotifications():
    try:
        wmx_files = os.listdir(folder)
        template_files = []
        for f in wmx_files:
            if f in ("settings___EmailNotifications.json", "EmailTemplate___ALL.json"):
                template_files.append(os.path.join(folder, f))

        if len(dest_wm.settings) == 0:
            for df in template_files:
                if "settings___EmailNotifications" in df:
                    with open(df, 'r') as w:
                        d = json.load(w)
                        result_update = dest_wm.update_settings(d)
                        if result_update:
                            arcpy.AddMessage("EmailNotifications update OK")
                        else:
                            arcpy.AddWarning("Error EmailNotifications")
                    break
        
        dest_wm_sgc = WorkflowManagerSgc(dest_wf_item)
        existing_templates = [x.template_name for x in dest_wm_sgc.email_templates]
        urlWfmService = dest_wm._url+"/templates/email?token="
        for df in template_files:
            if "EmailTemplate___ALL" in df:
                with open(df, 'r') as w:
                    d = json.load(w)
                    for t in d:
                        template_name = t['templateName']
                        if template_name not in existing_templates:
                            bodyParams = json.dumps(t)
                            result_update = ejecutarServicioWfm(urlWfmService, bodyParams)
                            if result_update and result_update.get('templateId'):
                                arcpy.AddMessage(f"EmailNotification {template_name} OK")
                            else:
                                arcpy.AddWarning(f"Error {template_name}, Error: {result_update}")
                        else:
                            arcpy.AddWarning(f"Email template {template_name} ya existente en destino")
    except Exception as ex:
        arcpy.AddMessage(str(ex))


def importLookupStatus():
    try:
        wmx_files = os.listdir(folder)
        template_files = []
        for f in wmx_files:
            if "lookups___status" in f:
                template_files.append(os.path.join(folder, f))
        
        status = dest_wm.lookups("status")
        existing_templates = [x["lookupName"] for x in status.lookups]
        for df in template_files:
            with open(df, 'r') as w:
                d = json.load(w)
                if len(existing_templates)>0:
                    arcpy.AddWarning(f"status {existing_templates} ya existentes en destino. Seran reemplazados por {d}")
                result_update = dest_wm.create_lookup("status", d["lookups"])
                if not result_update:
                    arcpy.AddWarning(f"Error {template_name}, Error: {result_update}")
        arcpy.AddMessage(f'\t...status imported successfully')
    except Exception as ex:
        arcpy.AddMessage(str(ex))


if __name__ == '__main__':
    importDiagrams()
    importJobTemplates()
    importEmailNotifications()
    importLookupStatus()
