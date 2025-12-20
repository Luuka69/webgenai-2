import TextInput from "../fields/TextInput";
import NumberInput from "../fields/NumberInput";
import DateInput from "../fields/DateInput";
import SelectInput from "../fields/SelectInput";
import ButtonField from "../fields/ButtonField";
import PasswordInput from "../fields/PasswordInput";
import EmailInput from "../fields/EmailInput"
import TextareaField from "../fields/TextareaField"
import CheckboxField from "../fields/CheckboxField";
import BooleanInput from "../fields/BooleanInput";
import TelInput from "../fields/TelInput";
import HiddenInput from "../fields/HiddenInput";
import Pagination from "../fields/Pagination";

export default function FieldWrapper({ element, editable, onSelect, value, onValueChange }) {
  const common = {
    label: element.ID_ELEMENT,
    required: element.VALIDATEUR_ELEMENT?.required,
    hint: element.HINT_ELEMENT,
    disabled: false,
    value,
    onChange: onValueChange, // ✅ IMPORTANT
  };

  let node = null;

  switch (element.TYPE_ELEMENT) {
    case "input_text":
      node = <TextInput {...common} />;
      break;
    case "input_number":
      node = <NumberInput {...common} />;
      break;
    case "input_date":
      node = <DateInput {...common} />;
      break;
    case "input_password":
      node = <PasswordInput {...common} />;
      break;
    case "input_email":
      node = <EmailInput {...common} />;
      break;
    case "select":
      node = <SelectInput {...common} options={element.ENUM_VALUES || []} />;
      break;
    case "button":
      node = <ButtonField label={element.ID_ELEMENT} />;
      break;
    case "textarea":
      node = <TextareaField {...common} />;
      break;
    case "input_checkbox":
      node = <CheckboxField {...common} />;
      break;
    case "input_boolean":
      node = <BooleanInput {...common} />;
      break;
    case "input_hidden":
      node = <HiddenInput {...common} />;
      break;
    case "input_tel":
      node = <TelInput {...common} />;
      break;
    case "pagination":
      node = <Pagination {...common} />;
      break;
    default:
      node = (
        <div className="text-sm text-gray-500">
          Unsupported TYPE_ELEMENT: <b>{element.TYPE_ELEMENT}</b>
        </div>
      );
  }

  return (
    <div
      onClick={() => editable && onSelect?.(element)}
      className={`rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition ${
        editable ? "cursor-pointer hover:ring-2 hover:ring-[#A744C3]/25" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="w-full">{node}</div>
        <div className="hidden sm:block text-xs text-gray-400 pt-1">
          {element.TYPE_ELEMENT}
        </div>
      </div>
    </div>
  );
}
