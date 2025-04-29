

import logging
from odoo import fields, models, tools
from odoo.tools.pycompat import to_text

_logger = logging.getLogger(__name__)

try:
    import ldap
    from ldap import modlist
except ImportError:
    _logger.debug("Cannot import ldap.")


class CompanyLDAP(models.Model):
    _inherit = "res.company.ldap"

    # 增加一个允许同步 mobile 字段的开关字段
    sync_to_mobile = fields.Boolean(
        string="同步办公手机到LDAP",
        help="如果启用，用户的公办手机字段改变将自动同步到LDAP的mobile属性."
    )
    # 增加一个允许同步 login 字段的开关字段
    sync_login_to_mail = fields.Boolean(
        string="同步login字段到LDAP",
        help="如果启用，用户的login字段改变将自动同步到LDAP的mail属性."
    )

    def _change_mobile(self, conf, login, new_mobile):
        """
        修改 LDAP 用户的 mobile 属性。
        :param conf: LDAP 配置
        :param login: 用户登录名
        :param new_mobile: 新的手机号码
        :return: 是否成功修改
        """
        changed = False
        # 根据用户的登录名（login）从 LDAP 中查找用户的 DN（Distinguished Name） 和 entry
        dn, entry = self._get_entry(conf, login)
        if not dn:
            _logger.error(f"User '{login}' not found in LDAP.")
            return False
        try:
            conn = self._connect(conf)
            # conn.simple_bind_s(dn, to_text(conf.get("ldap_password", "")))
            # 使用配置中有管理员账号和密码
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            #simple_bind_s方法用于执行 LDAP 绑定操作，验证绑定 DN 和密码是否有效。如果绑定成功，表示客户端已成功认证，可以执行后续的操作
            # conn.simple_bind_s(ldap_binddn, ldap_password)
            conn.simple_bind_s(to_text(ldap_binddn), to_text(ldap_password))
            # 构造修改操作
            # MOD_REPLACE 表示替换现有属性值
            mod_list = [
                (ldap.MOD_REPLACE, 'mobile', new_mobile.encode('utf-8'))
            ]
            # 执行修改操作
            conn.modify_s(dn, mod_list)
            changed = True
            _logger.info(f"Mobile number for user '{login}' updated successfully.")
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error("Invalid LDAP credentials for modifying mobile.")
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
        return changed

    def _change_email(self, conf, login, new_email):
        """
        修改 LDAP 用户的 mail 属性。
        :param conf: LDAP 配置
        :param login: 用户登录名
        :param new_email: 新的邮箱地址
        :return: 是否成功修改
        """
        changed = False
        # 根据用户的登录名（login）从 LDAP 中查找用户的 DN（Distinguished Name） 和 entry
        dn, entry = self._get_entry(conf, login)
        if not dn:
            _logger.error(f"User '{login}' not found in LDAP.")
            return False
        try:
            conn = self._connect(conf)
            # 使用配置中的管理员账号和密码进行绑定
            ldap_binddn = conf["ldap_binddn"] or ""
            ldap_password = conf["ldap_password"] or ""
            # simple_bind_s方法用于执行 LDAP 绑定操作，验证绑定 DN 和密码是否有效。如果绑定成功，表示客户端已成功认证，可以执行后续的操作
            conn.simple_bind_s(to_text(ldap_binddn), to_text(ldap_password))
            # 构造修改操作
            # MODIFY_REPLACE 表示替换现有属性值
            mod_list = [
                (ldap.MOD_REPLACE, 'mail', new_email.encode('utf-8'))
            ]
            # 执行修改操作
            conn.modify_s(dn, mod_list)
            changed = True
            _logger.info(f"Email address for user '{login}' updated successfully.")
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error("Invalid LDAP credentials for modifying email.")
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
        return changed

