# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models, fields, _
import re
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    group_value = fields.Integer( compute='_compute_group_value', default=0)
    gender1 = fields.Selection(related='gender',  string= '性别', readonly=False, related_sudo=False)
    place_of_birth1 = fields.Char(related='place_of_birth', string= '居住地址', readonly=False, related_sudo=False)
    marital1 = fields.Selection(related='marital', string= '婚姻状况', readonly=False, related_sudo=False)
    emergency_contact1 = fields.Char(related='emergency_contact',string= '紧急联系人', readonly=False, related_sudo=False)
    emergency_phone1 = fields.Char(related='emergency_phone', string= '紧急电话',readonly=False, related_sudo=False)

    @api.model
    def change_mobile(self, new_mobile):
        """
        修改当前用户的 LDAP mobile 属性。
        :param new_mobile: 新的手机号码
        :return: 是否成功修改
        """
        # 直接获取所有 LDAP 配置信息
        ldap_configs = (self.env['res.company.ldap'].sudo()
            .search([("ldap_server", "!=", False)], order="sequence")
            .read([]))
        for conf in ldap_configs:
            # 检查是否启用了同步开关
            if conf.get("sync_to_mobile", False):
                # 调用 _change_mobile 方法修改 LDAP 中的 mobile 属性
                Ldap = self.env['res.company.ldap']
                changed = Ldap._change_mobile(conf, self.env.user.login, new_mobile)
                if changed:
                    return True
        return False

    @api.model
    def change_email(self, user_id, new_email):
        """
        修改指定用户的 LDAP mail 属性。
        :param user_id: 用户的 ID
        :param new_email: 新的邮箱地址
        :return: 是否成功修改
        """
        # 直接获取所有 LDAP 配置信息
        ldap_configs = (self.env['res.company.ldap'].sudo()
            .search([("ldap_server", "!=", False)], order="sequence")
            .read([]))
        user = self.sudo().browse(user_id)  # 获取指定用户
        for conf in ldap_configs:
            # 检查是否启用了同步开关
            if conf.get("sync_login_to_mail", False):
                # 调用 _change_mobile 方法修改 LDAP 中的 mobile 属性
                Ldap = self.env['res.company.ldap']
                changed = Ldap._change_email(conf, user.login, new_email)
                if changed:
                    return True
        return False


    def _compute_group_value(self):
        # hr.group_hr_user对应’员工-主管‘组；hr.group_hr_manager对应’员工-管理员‘组
        for user in self:
            if user.user_has_groups('hr.group_hr_user') and not user.user_has_groups('hr.group_hr_manager'):
                user.group_value = 1
            elif user.user_has_groups('hr.group_hr_manager'):
                user.group_value = 2
            else:
                user.group_value = 0
    def link_user_to_employee(self):
        """
        遍历 res.users 模型的记录，检查 employee_id 是否为空。
        如果为空，尝试在 hr.employee 模型中查找 work_email 与 res.users 的 email 字段相等的记录。
        如果找到匹配的记录，则将 res.users 的 id 赋值给 hr.employee 的 user_id 字段。
        """
        # 获取所有 employee_id 为空的用户
        users = self.search([("employee_id", "=", False)])
        for user in users:
            if user.email:  # 确保用户有 email 字段
                # 在 hr.employee 中查找 work_email 与用户 email 相等的记录
                employee = self.env["hr.employee"].sudo().search([("work_email", "=", user.email)], limit=1)
                if employee:
                    # 将 res.users 的 id 赋值给 hr.employee 的 user_id 字段
                    employee.user_id = user.id

    def manual_link_user_to_employee(self):
        for user in self:
            if user.email and not user.employee_id:
                employee = self.env["hr.employee"].sudo().search([("work_email", "=", user.email)], limit=1)
                if employee:
                    employee.user_id = user.id
    def manual_unlink_user_to_employee(self):
        for user in self:
            if user.email and user.employee_id:
                employee = self.env["hr.employee"].sudo().search([("id", "=", user.employee_id.id)], limit=1)
                if employee:
                    employee.user_id = False
        return

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
            Access rights are disabled by default, but allowed
            on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        # 调用父类的__init__方法
        init_res=super(ResUsers, self).__init__(pool, cr)

        # 确保bank_ids和group_value字段添加到可写字段列表中
        new_fields = [
                    'bank_ids',
                    'gender1',
                    'place_of_birth1',
                    'marital1',
                    'emergency_contact1',
                    'emergency_phone1',
                    'group_value'
                    ]

        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(new_fields)

        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(new_fields)
        return init_res


    def write(self, vals):
        if vals:
            if vals and 'login' in vals:
                if self._is_valid_email(vals['login']):
                    # 如果邮箱格式正确，为每个用户调用 change_email 方法更新 LDAP 中的 mail 属性
                    for user in self:
                        user.change_email(user.id, vals['login'])
                else:
                    # 如果邮箱格式不正确，记录错误日志，但不抛出异常
                    _logger.error(f"Invalid email address: {vals['login']}")
            # 检查mobile_phone字段是否在vals中
            if 'mobile_phone' in vals:
                # 执行新的代码逻辑编辑mobile_phone字段
                for user in self:
                    if user.employee_id:
                        user.employee_id.sudo().mobile_phone = vals['mobile_phone']
                    if user.partner_id:
                        # 同步手机字段到联系人
                        user.partner_id.sudo().mobile = vals['mobile_phone']
                    # 调用 change_mobile 方法修改 LDAP 中的 mobile 属性
                    user.change_mobile(vals['mobile_phone'])
                # 将 mobile_phone 从 vals 中移除
                vals.pop('mobile_phone')
            if 'gender1' in vals:
                # 执行新的代码逻辑编辑gender字段
                for user in self:
                    if user.employee_id:
                        user.employee_id.sudo().gender = vals['gender1']
                # 将 gender1 从 vals 中移除
                vals.pop('gender1')
            if 'place_of_birth1' in vals:
                # 执行新的代码逻辑编辑place_of_birth字段
                for user in self:
                    if user.employee_id:
                        user.employee_id.sudo().place_of_birth = vals['place_of_birth1']
                # 将 place_of_birth1 从 vals 中移除
                vals.pop('place_of_birth1')
            if 'marital1' in vals:
                # 执行新的代码逻辑编辑marital字段
                for user in self:
                    if user.employee_id:
                        user.employee_id.sudo().marital = vals['marital1']
                # 将 marital1 从 vals 中移除
                vals.pop('marital1')
            if 'emergency_contact1' in vals:
                # 执行新的代码逻辑编辑emergency_contact字段
                for user in self:
                    if user.employee_id:
                        user.employee_id.sudo().emergency_contact = vals['emergency_contact1']
                # 将 emergency_contact1 从 vals 中移除
                vals.pop('emergency_contact1')

            if 'emergency_phone1' in vals:
                # 执行新的代码逻辑编辑emergency_phone字段
                for user in self:
                    if user.employee_id:
                        user.employee_id.sudo().emergency_phone = vals['emergency_phone1']
                # 将 emergency_phone1 从 vals 中移除
                vals.pop('emergency_phone1')
            # 调用父类的 write 方法以处理其他逻辑
            return super(ResUsers, self).write(vals)
        else:
            # 如果字段不在vals中，直接调用父类的write方法
            return super(ResUsers, self).write(vals)

    def _is_valid_email(self, email):
        """
        检查给定的字符串是否是有效的邮件地址。
        :param email: 待检查的字符串
        :return: 如果是有效的邮件地址，返回 True；否则返回 False
        """
        if not email:
            return False
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None
