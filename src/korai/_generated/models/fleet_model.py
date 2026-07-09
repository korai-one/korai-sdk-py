from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fleet_model_roles_item import FleetModelRolesItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fleet_model_variants import FleetModelVariants


T = TypeVar("T", bound="FleetModel")


@_attrs_define
class FleetModel:
    """
    Attributes:
        creator (str | Unset):
        license_ (str | Unset):
        family (str | Unset):
        total_params (str | Unset):
        active_params (str | Unset):
        context_len (int | Unset):
        multimodal (bool | Unset):
        roles (list[FleetModelRolesItem] | Unset):
        variants (FleetModelVariants | Unset):
    """

    creator: str | Unset = UNSET
    license_: str | Unset = UNSET
    family: str | Unset = UNSET
    total_params: str | Unset = UNSET
    active_params: str | Unset = UNSET
    context_len: int | Unset = UNSET
    multimodal: bool | Unset = UNSET
    roles: list[FleetModelRolesItem] | Unset = UNSET
    variants: FleetModelVariants | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        creator = self.creator

        license_ = self.license_

        family = self.family

        total_params = self.total_params

        active_params = self.active_params

        context_len = self.context_len

        multimodal = self.multimodal

        roles: list[str] | Unset = UNSET
        if not isinstance(self.roles, Unset):
            roles = []
            for roles_item_data in self.roles:
                roles_item = roles_item_data.value
                roles.append(roles_item)

        variants: dict[str, Any] | Unset = UNSET
        if not isinstance(self.variants, Unset):
            variants = self.variants.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if creator is not UNSET:
            field_dict["creator"] = creator
        if license_ is not UNSET:
            field_dict["license"] = license_
        if family is not UNSET:
            field_dict["family"] = family
        if total_params is not UNSET:
            field_dict["total_params"] = total_params
        if active_params is not UNSET:
            field_dict["active_params"] = active_params
        if context_len is not UNSET:
            field_dict["context_len"] = context_len
        if multimodal is not UNSET:
            field_dict["multimodal"] = multimodal
        if roles is not UNSET:
            field_dict["roles"] = roles
        if variants is not UNSET:
            field_dict["variants"] = variants

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fleet_model_variants import FleetModelVariants

        d = dict(src_dict)
        creator = d.pop("creator", UNSET)

        license_ = d.pop("license", UNSET)

        family = d.pop("family", UNSET)

        total_params = d.pop("total_params", UNSET)

        active_params = d.pop("active_params", UNSET)

        context_len = d.pop("context_len", UNSET)

        multimodal = d.pop("multimodal", UNSET)

        _roles = d.pop("roles", UNSET)
        roles: list[FleetModelRolesItem] | Unset = UNSET
        if _roles is not UNSET:
            roles = []
            for roles_item_data in _roles:
                roles_item = FleetModelRolesItem(roles_item_data)

                roles.append(roles_item)

        _variants = d.pop("variants", UNSET)
        variants: FleetModelVariants | Unset
        if isinstance(_variants, Unset):
            variants = UNSET
        else:
            variants = FleetModelVariants.from_dict(_variants)

        fleet_model = cls(
            creator=creator,
            license_=license_,
            family=family,
            total_params=total_params,
            active_params=active_params,
            context_len=context_len,
            multimodal=multimodal,
            roles=roles,
            variants=variants,
        )

        fleet_model.additional_properties = d
        return fleet_model

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
