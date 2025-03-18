from django_filters import filters


class CommaSeparatedValueFilter(filters.BaseCSVFilter, filters.CharFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        return qs.filter(**{f'{self.field_name}__in': value})
