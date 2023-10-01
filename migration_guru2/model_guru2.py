# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, SmallInteger, String, Table, Text, text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


t_current_event = Table(
    'current_event', metadata,
    Column('event_name', String(255, u'utf8_unicode_ci')),
    Column('event_end', Integer),
    Column('event_valid_from', Integer)
)


t_current_phonebook_tiny = Table(
    'current_phonebook_tiny', metadata,
    Column('extension', String(8, u'utf8_unicode_ci')),
    Column('ext_name', String(20, u'utf8_unicode_ci'))
)


class Dectset(Base):
    __tablename__ = 'dectsets'
    __table_args__ = (
        Index('event_name_2', 'event_name', 'IPUIN', 'IPUIO', unique=True),
    )

    id = Column(BigInteger, primary_key=True)
    username = Column(String(50, u'utf8_unicode_ci'), nullable=False, index=True)
    event_name = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    IPUIN = Column(String(14, u'utf8_unicode_ci'), nullable=False)
    IPUIO = Column(String(22, u'utf8_unicode_ci'), nullable=False)
    extension = Column(String(8, u'utf8_unicode_ci'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class DeleteRangelist(Base):
    __tablename__ = 'delete_rangelist'

    id = Column(BigInteger, primary_key=True)
    priority = Column(BigInteger, nullable=False)
    pattern = Column(String(1024, u'utf8_unicode_ci'), nullable=False)
    _del = Column('del', Integer, nullable=False, server_default=text("'0'"))
    comment = Column(String(2048, u'utf8_unicode_ci'))


class Event(Base):
    __tablename__ = 'events'

    id = Column(BigInteger, primary_key=True)
    event_name = Column(String(255, u'utf8_unicode_ci'), nullable=False, unique=True)
    event_location = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    event_start = Column(Integer, index=True)
    event_end = Column(Integer, index=True)
    event_valid_from = Column(Integer, index=True)
    ext_range_start = Column(Integer, nullable=False, server_default=text("'0'"))
    ext_range_end = Column(Integer, nullable=False, server_default=text("'0'"))
    orga_ext_range_start = Column(Integer, nullable=False, server_default=text("'0'"))
    orga_ext_range_end = Column(Integer, nullable=False, server_default=text("'0'"))
    pub_range = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    pub_range_blocklist = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    event_description_en = Column(String(collation=u'utf8_unicode_ci'), nullable=False)
    event_description_de = Column(String(collation=u'utf8_unicode_ci'), nullable=False)
    event_url = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    has_gsm = Column(Integer, nullable=False, server_default=text("'0'"))
    timestamp = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class IdentifiedUser(Base):
    __tablename__ = 'identified_users'

    username = Column(String(50, u'utf8_unicode_ci'), primary_key=True)
    terminal = Column(String(255, u'utf8_unicode_ci'), nullable=False, server_default=text("'0'"))
    logindate = Column(Integer, nullable=False, server_default=text("'0'"))
    timestamp = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class PermanentUserQueue(Base):
    __tablename__ = 'permanent_user_queue'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    event_id = Column(BigInteger, nullable=False)
    extension = Column(String(8, u'utf8_unicode_ci'), nullable=False)
    expire = Column(DateTime)
    email_sent = Column(Integer, nullable=False, server_default=text("'0'"))
    timestamp = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class PermissionName(Base):
    __tablename__ = 'permission_names'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    description = Column(String(255, u'utf8_unicode_ci'), nullable=False)


class PermissiongroupKey(Base):
    __tablename__ = 'permissiongroup_keys'

    id = Column(BigInteger, primary_key=True)
    key = Column(String(1024, u'utf8_unicode_ci'), nullable=False)
    default_value = Column(Integer, nullable=False, server_default=text("'0'"))
    name = Column(String(1024, u'utf8_unicode_ci'))


class PermissiongroupName(Base):
    __tablename__ = 'permissiongroup_names'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(1024, u'utf8_unicode_ci'))
    description = Column(String(1024, u'utf8_unicode_ci'), nullable=False)


class Permissiongroup(Base):
    __tablename__ = 'permissiongroups'
    __table_args__ = (
        Index('group_id', 'group_id', 'key_id', unique=True),
    )

    id = Column(BigInteger, primary_key=True)
    group_id = Column(BigInteger, nullable=False)
    key_id = Column(BigInteger, nullable=False)
    value = Column(Integer, nullable=False)


class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = (
        Index('user_id', 'user_id', 'permission_id', unique=True),
    )

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    permission_id = Column(BigInteger, nullable=False)
    permission_value = Column(Integer, nullable=False)


class Phonebook(Base):
    __tablename__ = 'phonebook'
    __table_args__ = (
        Index('IPUIN', 'IPUIN', 'IPUIO'),
        Index('extension', 'extension', 'event_name', unique=True)
    )

    id = Column(BigInteger, primary_key=True)
    extension = Column(String(8, u'utf8_unicode_ci'), nullable=False, server_default=text("'0'"))
    pub_alias = Column(String(8, u'utf8_unicode_ci'), nullable=False, index=True, server_default=text("''"))
    phone_type = Column(SmallInteger, nullable=False, index=True, server_default=text("'0'"))
    user = Column(String(50, u'utf8_unicode_ci'), nullable=False, index=True)
    event_id = Column(BigInteger, nullable=False)
    event_name = Column(String(255, u'utf8_unicode_ci'), nullable=False, index=True)
    ext_name = Column(String(20, u'utf8_unicode_ci'), nullable=False, index=True)
    location = Column(String(30, u'utf8_unicode_ci'), nullable=False, index=True)
    installed = Column(Integer, nullable=False, server_default=text("'0'"))
    alias_installed = Column(Integer, nullable=False, server_default=text("'0'"))
    ext_password = Column(String(30, u'utf8_unicode_ci'), nullable=False)
    phonebook_entry = Column(Integer, nullable=False, server_default=text("'1'"))
    abbrev_destination = Column(String(128, u'utf8_unicode_ci'))
    IPUIN = Column(String(14, u'utf8_unicode_ci'), nullable=False, server_default=text("''"))
    IPUIO = Column(String(22, u'utf8_unicode_ci'), nullable=False, server_default=text("''"))
    phone_type_description = Column(String(collation=u'utf8_unicode_ci'), nullable=False)
    ausleihnr = Column(String(32, u'utf8_unicode_ci'))
    timestamp = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    MAC = Column(String(12, u'utf8_unicode_ci'))


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(50, u'utf8_unicode_ci'), nullable=False, unique=True)
    password = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    md5password = Column(String(32, u'utf8_unicode_ci'), nullable=False)
    name = Column(String(50, u'utf8_unicode_ci'), nullable=False)
    firstname = Column(String(50, u'utf8_unicode_ci'), nullable=False)
    email = Column(String(255, u'utf8_unicode_ci'), nullable=False)
    callsign = Column(String(50, u'utf8_unicode_ci'), nullable=False)
    joined = Column(Integer)
    gcc = Column(Integer, nullable=False, server_default=text("'0'"))
    orga = Column(Integer, nullable=False, server_default=text("'0'"))
    admin = Column(Integer, nullable=False, server_default=text("'0'"))
    confirmed = Column(Integer, nullable=False, server_default=text("'0'"))
    comments = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)
    activation_key = Column(String(30, u'utf8_unicode_ci'), nullable=False, index=True, server_default=text("'0'"))
    timestamp = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    permissiongroup_id = Column(BigInteger)
