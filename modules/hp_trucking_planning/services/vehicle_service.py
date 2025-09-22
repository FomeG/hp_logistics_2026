from odoo.addons.hp_components.models import constants

class VehicleService:
    _name = "vehicle.service"

    VEHICLE_MODEL_TYPE_TRUCK = 'truck'
    VEHICLE_MODEL_TYPE_TRAILER = 'trailer'

    VEHICLE_ENGINE_TYPE_SMALL = 'small'
    VEHICLE_ENGINE_TYPE_BIG = 'big'

    def __init__(self, env):
        self.env = env

    def _get_or_create_vehicle_model_category_by_name(self, category_name):
        VehicleModelCategory = self.env['fleet.vehicle.model.category']
        category = VehicleModelCategory.search([('name', '=', category_name)], limit=1)

        if not category:
            category = VehicleModelCategory.create({
                'name': category_name,
            })
        return category

    def _get_or_create_vehicle_model_brand_by_name(self, brand_name):
        VehicleModelBrand = self.env['fleet.vehicle.model.brand']
        brand = VehicleModelBrand.search([('name','=', brand_name)], limit=1)
        if not brand:
            brand = VehicleModelBrand.create({
                'name': brand_name,
            })
        return brand

    def _get_or_create_vehicle_model_by_name(self, model_name):
        VehicleModel = self.env['fleet.vehicle.model']
        model = VehicleModel.search([('name', '=', model_name)], limit=1)

        if not model:
            brand = self._get_or_create_vehicle_model_brand_by_name(model_name)
            category = self._get_or_create_vehicle_model_category_by_name(model_name)
            model = VehicleModel.create({
                'name': model_name,
                'brand_id':brand.id,
                'category_id': category.id,
            })
        return model

    def _check_vehicle_category(self, vehicle, category_name):
        if not vehicle or not vehicle.category_id:
            return False
        vehicle_model_category = self._get_or_create_vehicle_model_category_by_name(category_name)
        return vehicle.category_id.id == vehicle_model_category.id

    def is_truck(self, vehicle):
        return self._check_vehicle_category(vehicle, constants.VehicleModelCategory.TRUCK)

    def is_trailer(self, vehicle):
        return self._check_vehicle_category(vehicle, constants.VehicleModelCategory.TRAILER)

    def _compute_vehicle_model(self, vehicle, category_name = constants.VehicleModel.TRUCK):
        model = self._get_or_create_vehicle_model_by_name(category_name)
        vehicle.model_id = model.id

    def _compute_vehicle_category(self, vehicle, category_name = constants.VehicleModelCategory.TRUCK):
        category = self._get_or_create_vehicle_model_category_by_name(category_name)
        vehicle.category_id = category.id

    def set_truck(self, vehicle):
        if not self.is_truck(vehicle):
            self._compute_vehicle_model(vehicle)
            self._compute_vehicle_category(vehicle)


    def set_trailer(self, vehicle):
        if not self.is_trailer(vehicle):
            self._compute_vehicle_model(vehicle, constants.VehicleModel.TRAILER)
            self._compute_vehicle_category(vehicle, constants.VehicleModelCategory.TRAILER)

    # engine type
    def _get_or_create_vehicle_tag_by_name(self, tag_name):
        VehicleTag = self.env['fleet.vehicle.tag']
        tag = VehicleTag.search([('name', '=', tag_name)], limit=1)
        if not tag:
            tag = VehicleTag.create({
                'name': tag_name,
            })
        return tag

    def _check_vehicle_tag(self, vehicle, tag_name):
        if not vehicle or not vehicle.tag_ids :
            return False
        tag = self._get_or_create_vehicle_tag_by_name(tag_name)
        return tag.id in vehicle.tag_ids.ids

    def is_big_engine(self, vehicle_hpl):
        return self._check_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.ENGINE_BIG)

    def is_small_engine(self, vehicle_hpl):
        return self._check_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.ENGINE_SMALL)

    # is rented
    def is_rented(self, vehicle_hpl):
        return self._check_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.RENTED)

    def _compute_vehicle_tag(self, vehicle, tag_name, action = 'add'):
        vehicle_tag = self._get_or_create_vehicle_tag_by_name(tag_name)
        if action == 'add':
            vehicle.write({'tag_ids': [(4, vehicle_tag.id)]})
        else:
            vehicle.write({'tag_ids': [(3, vehicle_tag.id)]})

    def set_big_engine(self, vehicle_hpl):
        if not self.is_big_engine(vehicle_hpl):
            self._compute_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.ENGINE_BIG)
            self._compute_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.ENGINE_SMALL, action = 'remove')

    def set_small_engine(self, vehicle_hpl):
        if not self.is_small_engine(vehicle_hpl):
            self._compute_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.ENGINE_SMALL)
            self._compute_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.ENGINE_BIG, action = 'remove')
    def set_rented(self, vehicle_hpl):
        if not self.is_rented(vehicle_hpl):
            self._compute_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.RENTED)

    def remove_rented(self, vehicle_hpl):
        if self.is_rented(vehicle_hpl):
            self._compute_vehicle_tag(vehicle_hpl.vehicle_id, constants.VehicleTag.RENTED, action='remove')

    def init_hpl_data_by_type(self, vehicle_type):
        if vehicle_type == constants.VehicleModelCategory.TRUCK:
            model = self._get_or_create_vehicle_model_by_name(constants.VehicleModel.TRUCK)
        else:
            model = self._get_or_create_vehicle_model_by_name(constants.VehicleModel.TRAILER)
        return {
            'model_id': model.id,
            'category_id': model.category_id.id,
        }
