import logging

_logger = logging.getLogger(__name__)

class ActivityService:

    def __init__(self, env, model_name, record_id, user_ids):
        self.env = env
        self.model_name = model_name
        self.record_id = record_id
        # accept single user or list
        self.user_ids = user_ids if isinstance(user_ids, (list, tuple)) else [user_ids]

    def _create_activity_by_type(self, activity_type_xml_id = 'mail.mail_activity_data_todo', summary='', note=''):
        model = self.env['ir.model']._get(self.model_name)
        activity_type = self.env.ref(activity_type_xml_id)

        # Handle both single user_id and list of user_ids
        user_ids = self.user_ids if isinstance(self.user_ids, (list, tuple)) else [self.user_ids]

        # Batch create: collect all activity vals
        activity_vals_list = [
            {
                'activity_type_id': activity_type.id,
                'note': note or summary,
                'res_id': self.record_id,
                'res_model_id': model.id,
                'user_id': uid,
                'summary': summary,
            }
            for uid in user_ids
        ]

        if activity_vals_list:
            self.env['mail.activity'].create(activity_vals_list)

    def create_price_request(self, summary='', note=''):
        self._create_activity_by_type(summary=summary,note=note)
    #todo: when task done => set done
    def mark_done_by_task(self, task):
        _logger.info('Marking activity as done')
    # todo: when task cancel => set cancel
    def mark_cancel_by_task(self, task):
        _logger.info('Marking activity as cancel')