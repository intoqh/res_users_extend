# -*- coding: utf-8 -*-
from odoo import models
from odoo import api, fields, models, tools, _

class Partner(models.Model):

    _inherit = ['res.partner']

    # 同步手机字段到员工
    def write(self, vals):
        # 检查 mobile 是否在 vals 中
        if 'mobile' in vals and not self.env.context.get('update_employee_mobile'):
            new_mobile = vals['mobile']
            # 遍历当前 partner 的所有关联用户
            for partner in self:
                for user in partner.user_ids:
                    # 检查用户是否有关联的雇员
                    if user.employee_id:  # 使用 employee_id
                        # 更新雇员的 mobile_phone 字段
                        # 使用上下文标志避免递归调用
                        user.employee_id.with_context(update_partner_mobile=True).write({'mobile_phone': new_mobile})

        # 调用父类的 write 方法
        return super(Partner, self).write(vals)






