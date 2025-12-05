from ...hp_components.models.constants import ServiceType

class CsOrderService:
    _name = "cs.order.service"

    def __init__(self, env):
        self.env = env


    def get_project_task_type_by_service_type(self, service_type):
        xml_ids_map = {
            ServiceType.IMPORT: [
                'hp_customer_service.stage_before_departure',
                'hp_customer_service.stage_sailing',
                'hp_customer_service.stage_docking',
                'hp_customer_service.stage_unloading',
            ],
            ServiceType.EXPORT: [
                'hp_customer_service.stage_before_departure',
                'hp_customer_service.stage_sailing',
                'hp_customer_service.stage_after_departure',
            ],
        }

        xml_ids = xml_ids_map.get(service_type, [])
        stages = self.env['project.task.type']
        for xml_id in xml_ids:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                stages |= stage
        return stages
    
    def assgin_project_task_type_to_cs_order_project(self, cs_order):
        project = cs_order.project_id
        if not project:
            return False

        project_task_types = self.get_project_task_type_by_service_type(cs_order.service_type)
        project.type_ids = [(6, 0, project_task_types.ids)]

        return cs_order