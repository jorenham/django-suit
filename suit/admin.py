import copy

from django import forms
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes import admin as ct_admin
from django.db.models import Max

from suit.widgets import NumberInput, SuitSplitDateTimeWidget


class SortableModelAdminBase:
    """
    Base class for SortableTabularInline and SortableModelAdmin
    """
    sortable = 'order'

    class Media:
        js = ('suit/js/sortables.js',)


class SortableListForm(forms.ModelForm):
    """
    Just Meta holder class
    """

    class Meta:
        widgets = {
            'order': NumberInput(
                attrs={'class': 'hide input-mini suit-sortable'},
            )
        }


class SortableChangeList(ChangeList):
    """
    Class that forces ordering by sortable param only
    """

    def get_ordering(self, request, queryset):
        return [self.model_admin.sortable, '-' + self.model._meta.pk.name]


class SortableTabularInlineBase(SortableModelAdminBase):
    """
    Sortable tabular inline
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ordering = (self.sortable,)
        self.fields = self.fields or []
        if self.fields and self.sortable not in self.fields:
            self.fields = list(self.fields) + [self.sortable]

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == self.sortable:
            kwargs['widget'] = SortableListForm.Meta.widgets['order']
        return super().formfield_for_dbfield(db_field, **kwargs)


class SortableTabularInline(
    SortableTabularInlineBase, 
    admin.TabularInline,
):
    pass


class SortableGenericTabularInline(
    SortableTabularInlineBase,
    ct_admin.GenericTabularInline,
):
    pass


class SortableStackedInlineBase(SortableModelAdminBase):
    def get_fieldsets(self, *args, **kwargs):
        """
        Iterate all fieldsets and make sure sortable is in the first fieldset
        Remove sortable from every other fieldset, if by some reason someone
        has added it
        """
        fieldsets = super().get_fieldsets(*args, **kwargs)

        sortable_added = False
        for fieldset in fieldsets:
            for line in fieldset:
                if not line or not isinstance(line, dict):
                    continue

                fields = line.get('fields')

                # Some use tuples for fields however they are immutable
                if isinstance(fields, tuple):
                    raise TypeError(
                        "The fields attribute of your Inline is a tuple. "
                        "This must be list as we may need to modify it and "
                        "tuples are immutable."
                    )

                if self.sortable in fields:
                    fields.remove(self.sortable)

                # Add sortable field always as first
                if not sortable_added:
                    fields.insert(0, self.sortable)
                    sortable_added = True
                    break

        return fieldsets

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == self.sortable:
            kwargs['widget'] = copy.deepcopy(
                SortableListForm.Meta.widgets['order']
            )
            kwargs['widget'].attrs['class'] += ' suit-sortable-stacked'
            kwargs['widget'].attrs['rowclass'] = ' suit-sortable-stacked-row'
        return super().formfield_for_dbfield(db_field, **kwargs)


class SortableStackedInline(
    SortableStackedInlineBase, 
    admin.StackedInline,
):
    pass


class SortableGenericStackedInline(
    SortableStackedInlineBase,
    ct_admin.GenericStackedInline,
):
    pass


class SortableModelAdmin(SortableModelAdminBase, admin.ModelAdmin):
    list_per_page = 500

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ordering = (self.sortable,)
        if self.list_display and self.sortable not in self.list_display:
            self.list_display = list(self.list_display) + [self.sortable]

        self.list_editable = self.list_editable or []
        if self.sortable not in self.list_editable:
            self.list_editable = list(self.list_editable) + [self.sortable]

        self.exclude = self.exclude or []
        if self.sortable not in self.exclude:
            self.exclude = list(self.exclude) + [self.sortable]

    def merge_form_meta(self, form):
        """
        Prepare Meta class with order field widget
        """
        if not getattr(form, 'Meta', None):
            form.Meta = SortableListForm.Meta
        if not getattr(form.Meta, 'widgets', None):
            form.Meta.widgets = {}
        form.Meta.widgets[self.sortable] = SortableListForm.Meta.widgets['order']

    def get_changelist_form(self, request, **kwargs):
        form = super().get_changelist_form(request, **kwargs)
        self.merge_form_meta(form)
        return form

    def get_changelist(self, request, **kwargs):
        return SortableChangeList

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            next_order = type(obj).objects.aggregate(
                _max_order_value=Max(self.sortable, default=0),
            )['_max_order_value'] + 1
            setattr(obj, self.sortable, next_order)
        super().save_model(request, obj, form, change)
