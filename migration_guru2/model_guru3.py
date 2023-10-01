# coding: utf-8
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class AuthGroup(Base):
    __tablename__ = 'auth_group'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)


class AuthGroupPermission(Base):
    __tablename__ = 'auth_group_permissions'
    __table_args__ = (
        Index('auth_group_permissions_group_id_permission_id_0cd325b0_uniq', 'group_id', 'permission_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey(u'auth_group.id'), nullable=False)
    permission_id = Column(ForeignKey(u'auth_permission.id'), nullable=False, index=True)

    group = relationship(u'AuthGroup')
    permission = relationship(u'AuthPermission')


class AuthPermission(Base):
    __tablename__ = 'auth_permission'
    __table_args__ = (
        Index('auth_permission_content_type_id_codename_01ab375a_uniq', 'content_type_id', 'codename', unique=True),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    content_type_id = Column(ForeignKey(u'django_content_type.id'), nullable=False)
    codename = Column(String(100), nullable=False)

    content_type = relationship(u'DjangoContentType')


class AuthUser(Base):
    __tablename__ = 'auth_user'

    id = Column(Integer, primary_key=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime)
    is_superuser = Column(Integer, nullable=False)
    username = Column(String(150), nullable=False, unique=True)
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(254), nullable=False)
    is_staff = Column(Integer, nullable=False)
    is_active = Column(Integer, nullable=False)
    date_joined = Column(DateTime, nullable=False)


class AuthUserGroup(Base):
    __tablename__ = 'auth_user_groups'
    __table_args__ = (
        Index('auth_user_groups_user_id_group_id_94350c0c_uniq', 'user_id', 'group_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(u'auth_user.id'), nullable=False)
    group_id = Column(ForeignKey(u'auth_group.id'), nullable=False, index=True)

    group = relationship(u'AuthGroup')
    user = relationship(u'AuthUser')


class AuthUserUserPermission(Base):
    __tablename__ = 'auth_user_user_permissions'
    __table_args__ = (
        Index('auth_user_user_permissions_user_id_permission_id_14a6b632_uniq', 'user_id', 'permission_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(u'auth_user.id'), nullable=False)
    permission_id = Column(ForeignKey(u'auth_permission.id'), nullable=False, index=True)

    permission = relationship(u'AuthPermission')
    user = relationship(u'AuthUser')


class CoreDecthandset(Base):
    __tablename__ = 'core_decthandset'

    id = Column(Integer, primary_key=True)
    description = Column(String(64), nullable=False)
    enableEncryption = Column(Integer, nullable=False)
    owner_id = Column(ForeignKey(u'auth_user.id'), index=True)

    owner = relationship(u'AuthUser')


class CoreEvent(Base):
    __tablename__ = 'core_event'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    location = Column(String(128), nullable=False)
    eventStreamTarget = Column(String(256), nullable=False)
    start = Column(Date)
    end = Column(Date)
    registrationStart = Column(Date)
    extensionLength = Column(Integer, nullable=False)
    extensionStart = Column(String(32), nullable=False)
    extensionEnd = Column(String(32), nullable=False)
    orgaExtensionStart = Column(String(32), nullable=False)
    orgaExtensionEnd = Column(String(32), nullable=False)
    hasGSM = Column(Integer, nullable=False)
    descriptionDE = Column(String, nullable=False)
    descriptionEN = Column(String, nullable=False)
    url = Column(String(200), nullable=False)


class CoreExtension(Base):
    __tablename__ = 'core_extension'

    id = Column(Integer, primary_key=True)
    lastChanged = Column(DateTime, nullable=False)
    type = Column(String(16), nullable=False)
    extension = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)
    inPhonebook = Column(Integer, nullable=False)
    isInstalled = Column(Integer, nullable=False)
    location = Column(String(64), nullable=False)
    registerToken = Column(String(32), nullable=False)
    displayModus = Column(String(16), nullable=False)
    sipPassword = Column(String(16), nullable=False)
    isPremium = Column(Integer, nullable=False)
    event_id = Column(ForeignKey(u'core_event.id'), nullable=False, index=True)
    handset_id = Column(ForeignKey(u'core_decthandset.id'), index=True)
    owner_id = Column(ForeignKey(u'auth_user.id'), index=True)
    useEncryption = Column(Integer, nullable=False)

    event = relationship(u'CoreEvent')
    handset = relationship(u'CoreDecthandset')
    owner = relationship(u'AuthUser')


class CoreUserapikey(Base):
    __tablename__ = 'core_userapikey'

    id = Column(Integer, primary_key=True)
    key = Column(String(64), nullable=False)
    user_id = Column(ForeignKey(u'auth_user.id'), nullable=False, index=True)

    user = relationship(u'AuthUser')


class CoreWiremessage(Base):
    __tablename__ = 'core_wiremessage'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    delivered = Column(Integer, nullable=False)
    type = Column(String(16), nullable=False)
    data = Column(String, nullable=False)
    event_id = Column(ForeignKey(u'core_event.id'), nullable=False, index=True)

    event = relationship(u'CoreEvent')


class DjangoAdminLog(Base):
    __tablename__ = 'django_admin_log'

    id = Column(Integer, primary_key=True)
    action_time = Column(DateTime, nullable=False)
    object_id = Column(String)
    object_repr = Column(String(200), nullable=False)
    action_flag = Column(SmallInteger, nullable=False)
    change_message = Column(String, nullable=False)
    content_type_id = Column(ForeignKey(u'django_content_type.id'), index=True)
    user_id = Column(ForeignKey(u'auth_user.id'), nullable=False, index=True)

    content_type = relationship(u'DjangoContentType')
    user = relationship(u'AuthUser')


class DjangoContentType(Base):
    __tablename__ = 'django_content_type'
    __table_args__ = (
        Index('django_content_type_app_label_model_76bd3d3b_uniq', 'app_label', 'model', unique=True),
    )

    id = Column(Integer, primary_key=True)
    app_label = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)


class DjangoMigration(Base):
    __tablename__ = 'django_migrations'

    id = Column(Integer, primary_key=True)
    app = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    applied = Column(DateTime, nullable=False)


class DjangoSession(Base):
    __tablename__ = 'django_session'

    session_key = Column(String(40), primary_key=True)
    session_data = Column(String, nullable=False)
    expire_date = Column(DateTime, nullable=False, index=True)


class RegistrationRegistrationprofile(Base):
    __tablename__ = 'registration_registrationprofile'

    id = Column(Integer, primary_key=True)
    activation_key = Column(String(40), nullable=False)
    user_id = Column(ForeignKey(u'auth_user.id'), nullable=False, unique=True)

    user = relationship(u'AuthUser')
