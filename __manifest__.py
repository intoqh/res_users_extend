# -*- coding: utf-8 -*-
{
    'name': "用户功能扩展",
    'summary': """用户功能扩展""",
    'description': """用户功能扩展""",
    'author': "Bill yang",
    'category': 'Human Resources/Employees',
    'version': '14.0.7.0.0',
    'depends': ["hr","auth_ldap"],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'data/res_users_data.xml',
        'views/res_users_views.xml',
        'views/res_company_ldap.xml',
    ],
    'qweb': [
        'static/src/xml/user_templates.xml',
    ],
    'license': 'LGPL-3',
}
