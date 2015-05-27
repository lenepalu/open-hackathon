# -*- coding: utf-8 -*-
"""
Copyright (c) Microsoft Open Technologies (Shanghai) Co. Ltd.  All rights reserved.
 
The MIT License (MIT)
 
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import sys

sys.path.append("..")
from hackathon.database import db_adapter
from hackathon.database.models import AdminHackathonRel, User, UserEmail, Hackathon
from flask import g
from hackathon.hackathon_response import *
from hackathon.functions import get_now
from hackathon.user.user_mgr import user_manager


class AdminManager(object):
    def __init__(self, db_adapter):
        self.db = db_adapter

    def get_hackathon_admin_with_email(self):
        # only returns the primary email
        return self.db.session().query(AdminHackathonRel).join(User) \
            .filter(AdminHackathonRel.hackathon_id==g.hackathon.id) \
            .all()

    def get_hackathon_admins(self):
        def to_dict(ahl):
            dic = ahl.dic()
            dic["user_info"] = user_manager.user_display_info(ahl.user)
            return dic
        x= map(lambda ahl: to_dict(ahl), self.get_hackathon_admin_with_email())
        return x

    def validate_created_args(self, args):
        if 'email' not in args:
            return False, bad_request("email invalid")

        user_email = self.db.find_first_object(UserEmail, UserEmail.email == args['email'])
        if user_email is None:
            return False, not_found("email does not exist in DB")

        uid = user_email.user.id
        hid = g.hackathon.id
        ahl = self.db.find_first_object(AdminHackathonRel, AdminHackathonRel.user_id == uid,
                                        AdminHackathonRel.hackathon_id == hid)
        if ahl is not None:
            return True, 'aleady exist'

        return True, 'passed'


    def create_admin(self, args):
        # validate args
        status, info = self.validate_created_args(args)
        if not status:
            return info
        elif info == 'aleady exist':
            return ok()

        try:
            user_email = self.db.find_first_object(UserEmail, UserEmail.email == args['email'])
            ahl = AdminHackathonRel(user_id=user_email.user.id,
                                    role_type=args['role_type'],
                                    hackathon_id=g.hackathon.id,
                                    status=1,
                                    remarks=args['remarks'],
                                    create_time=get_now())
            self.db.add_object(ahl)
            return ok()
        except Exception as e:
            log.error(e)
            return internal_server_error("create admin failed")


    def update_admin(self, args):
        ahl = self.db.find_first_object(AdminHackathonRel, AdminHackathonRel.id==args['id'])
        update_items = dict(dict(args).viewitems() - ahl.dic().viewitems())
        update_items.pop('user_id', 'pass')
        update_items.pop('hackathon_id', 'pass')
        update_items.pop('email', 'pass')
        update_items['update_time'] = get_now()
        try:
            self.db.update_object(ahl, **update_items)
            return ok('update ahl success')
        except Exception as e:
            log.error(e)
            return internal_server_error(e)


    def delete_admin(self, ahl_id):
        ahl = self.db.find_first_object(AdminHackathonRel, AdminHackathonRel.id==ahl_id)

        if ahl is None:
            return ok()

        hackathon = self.db.find_first_object(Hackathon, Hackathon.id == ahl.hackathon_id)
        if hackathon.creator_id == ahl.user_id:
            return bad_request("hackathon creatore can not be deleted")

        try :
            self.db.delete_object(ahl)
            return ok()
        except Exception as e:
            log.error(e)
            return internal_server_error(e)


admin_manager = AdminManager(db_adapter)