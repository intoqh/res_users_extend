# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models ,fields, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re

class HrEmployee(models.Model):
    _inherit = "hr.employee"


    #同步手机字段到联系人
    def write(self, vals):
        # 检查 mobile_phone 是否在 vals 中
        if 'mobile_phone' in vals and not self.env.context.get('update_partner_mobile'):
            new_mobile_phone = vals['mobile_phone']
            # 检查是否存在 user_partner_id 并更新其 phone 字段
            if self.user_partner_id:
                # 使用上下文标志避免递归调用
                self.user_partner_id.with_context(update_employee_mobile=True).write({'mobile': new_mobile_phone})
            elif self.address_home_id:
                self.address_home_id.with_context(update_employee_mobile=True).write({'mobile': new_mobile_phone})

        # 调用父类的 write 方法
        return super(HrEmployee, self).write(vals)