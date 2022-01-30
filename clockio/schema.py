import graphene
import graphql_jwt

from clockio.memories.gql import MemoryMutation, MemoryClockOutMutation, MemoryType, CurrentClockType, ClockedHourType
from clockio.memories.models import Memory
from clockio.users.gql import UserMutation, UserType


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    current_clock = graphene.Field(CurrentClockType)
    clocked_hours = graphene.Field(ClockedHourType)

    def resolve_current_clock(self, info, *args, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication credentials were not provided")
        return Memory.objects.last()

    def resolve_me(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication credentials were not provided")
        return user

    def resolve_clocked_hours(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication credentials were not provided")
        return Memory()     # No need to hit database just use dummy.


class Mutation(graphene.ObjectType):
    obtain_token = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    create_user = UserMutation.Field()
    clock_in = MemoryMutation.Field()
    clock_out = MemoryClockOutMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
