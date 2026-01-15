export default function HiddenInput({ value }) {
  // input hidden — no UI
  return <input type="hidden" value={value ?? ""} readOnly />;
}
