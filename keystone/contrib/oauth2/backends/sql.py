# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystone.common import sql
from keystone.contrib import oauth2
from keystone import exception
from keystone.i18n import _
import uuid

class Consumer(sql.ModelBase, sql.ModelDictMixin):
    __tablename__ = 'consumer'
    attributes = ['id', 'description','secret','client_type', 'redirect_uris',
                    'grant_type','response_type','scopes']
                    
    id = sql.Column(sql.String(64), primary_key=True, nullable=False)
    description = sql.Column(sql.String(64), nullable=True)
    secret = sql.Column(sql.String(64), nullable=False)
    client_type = sql.Column(sql.Enum('confidential'),nullable=False) #TODO set as configuration option in keystone.conf
    redirect_uris = sql.Column(sql.JsonBlob(), nullable=False)
    grant_type = sql.Column(sql.Enum('authorization_code'),nullable=False) #TODO set as configuration option in keystone.conf
    response_type = sql.Column(sql.Enum('code'),nullable=False) #TODO set as configuration option in keystone.conf
    scopes = sql.Column(sql.JsonBlob(),nullable=True)
    #extra = sql.Column(sql.JsonBlob(), nullable=False)

class AuthorizationCode(sql.ModelBase, sql.ModelDictMixin):
    __tablename__ = 'authorization_code'

    code = sql.Column(sql.String(64),primary_key=True,nullable=False)
    consumer_id = sql.Column(sql.String(64), sql.ForeignKey('consumer.id'),
                             nullable=False, index=True)
    authorizing_user_id = sql.Column(sql.String(64), nullable=False)#TODO shouldnt it be a Foreign Key??
    expires_at = sql.Column(sql.String(64), nullable=False)#TODO datetime type or similar?
    scopes = sql.Column(sql.JsonBlob(),nullable=True)

class OAuth2(oauth2.Driver):
    """ CRUD driver for the SQL backend """
    def _get_consumer(self, session, consumer_id):
        consumer_ref = session.query(Consumer).get(consumer_id)
        if consumer_ref is None:
            raise exception.NotFound(_('Consumer not found'))
        return consumer_ref
    def list_consumers(self):
        session = sql.get_session()
        cons = session.query(Consumer)
        return [consumer.to_dict() for consumer in cons]

    def create_consumer(self,consumer):
        consumer['secret'] = uuid.uuid4().hex
        if not consumer.get('description'):
            consumer['description'] = None
        session = sql.get_session()
        #set the response_type based on the grant_type
        if consumer['grant_type'] == 'authorization_code':
            consumer['response_type'] = 'code'
        with session.begin():
            consumer_ref = Consumer.from_dict(consumer)
            session.add(consumer_ref)
        return consumer_ref.to_dict()

    def get_consumer(self,consumer_id):
        session = sql.get_session()
        with session.begin():
            consumer_ref = self._get_consumer(session,consumer_id)
        return consumer_ref.to_dict()

    def update_consumer(self,consumer_id,consumer):
        session = sql.get_session()
        with session.begin():
            consumer_ref = self._get_consumer(session, consumer_id)
            old_consumer_dict = consumer_ref.to_dict()
            old_consumer_dict.update(consumer)
            new_consumer = Consumer.from_dict(old_consumer_dict)
        return new_consumer.to_dict()

    def delete_consumer(self, consumer_id):
        session = sql.get_session()
        with session.begin():
            self._delete_consumer(session, consumer_id)

    def _delete_consumer(self, session, consumer_id):
        consumer_ref = self._get_consumer(session, consumer_id)
        session.delete(consumer_ref)

    def list_authorization_codes(self):
        session = sql.get_session()
        cons = session.query(AuthorizationCode)
        return [authorization_code.to_dict() for authorization_code in cons]
