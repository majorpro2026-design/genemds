import { icon, escapeAttr, escapeHtml } from '../utils/dom'

export type PatientDetails = {
  fullName: string
  dobDay: string
  dobMonth: string
  dobYear: string
  sex: string
}

const PATIENT_ENDPOINT = import.meta.env.VITE_PATIENT_API_URL ?? '/api/patients'
const SEX_OPTIONS = ['Female', 'Male', 'Other']

let patient: PatientDetails = { fullName: '', dobDay: '', dobMonth: '', dobYear: '', sex: '' }
let patientId: number | null = null
let saving = false
let saveError = ''

export function getPatientId() {
  return patientId
}

function composeDob(): string | null {
  const day = Number(patient.dobDay)
  const month = Number(patient.dobMonth)
  const year = Number(patient.dobYear)
  const currentYear = new Date().getFullYear()
  if (!day || !month || !year) return null
  if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900 || year > currentYear) return null
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

export function isPatientComplete() {
  return Boolean(patient.fullName.trim() && composeDob() && patient.sex)
}

export function resetPatient() {
  patient = { fullName: '', dobDay: '', dobMonth: '', dobYear: '', sex: '' }
  patientId = null
  saving = false
  saveError = ''
}

export function syncPatientField(target: HTMLInputElement | HTMLSelectElement) {
  const field = target.dataset.patientField as keyof PatientDetails | undefined
  if (!field) return
  patient[field] = target.value
}

export function patientStep() {
  return `
    <section class="card patient-card">
      <div class="card-title">
        <div>
          <h2>Patient details</h2>
          <p>Enter the patient's information to start a new prescription.</p>
        </div>
      </div>

      <div class="form-grid">
        <label>Full name <b>*</b>
          <input data-patient-field="fullName" placeholder="e.g. Jane Doe" value="${escapeAttr(patient.fullName)}">
        </label>
        <label>Date of birth <b>*</b>
          <div class="dob-fields">
            <input data-patient-field="dobDay" type="text" inputmode="numeric" pattern="[0-9]*" placeholder="DD" maxlength="2" value="${escapeAttr(patient.dobDay)}">
            <input data-patient-field="dobMonth" type="text" inputmode="numeric" pattern="[0-9]*" placeholder="MM" maxlength="2" value="${escapeAttr(patient.dobMonth)}">
            <input data-patient-field="dobYear" type="text" inputmode="numeric" pattern="[0-9]*" placeholder="YYYY" maxlength="4" value="${escapeAttr(patient.dobYear)}">
          </div>
        </label>
        <label>Sex <b>*</b>
          <select data-patient-field="sex">
            <option value="">Select sex</option>
            ${SEX_OPTIONS.map(value => `<option ${patient.sex === value ? 'selected' : ''}>${value}</option>`).join('')}
          </select>
        </label>
      </div>

      ${saveError ? `<div class="submission-error">${escapeHtml(saveError)}</div>` : ''}

      <footer class="card-footer">
        <span class="completion-note">${isPatientComplete() ? 'Patient details are complete.' : 'Full name, date of birth, and sex are required.'}</span>
        <button class="primary" data-action="save-patient" ${isPatientComplete() && !saving ? '' : 'disabled'}>${saving ? '<span class="spinner"></span> Saving...' : `Continue ${icon('arrow')}`}</button>
      </footer>
    </section>
  `
}

export async function createPatient(): Promise<boolean> {
  const dob = composeDob()
  if (!isPatientComplete() || saving || !dob) return false

  saving = true
  saveError = ''

  try {
    const response = await fetch(PATIENT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ fullName: patient.fullName.trim(), dob, sex: patient.sex }),
    })

    if (!response.ok) {
      throw new Error(`Patient save failed with status ${response.status}`)
    }

    const body = (await response.json()) as { patientId?: number }
    if (typeof body.patientId !== 'number') {
      throw new Error('Patient save response was missing a patient ID.')
    }

    patientId = body.patientId
    return true
  } catch (error) {
    saveError = error instanceof Error ? error.message : 'Unexpected error while saving the patient.'
    return false
  } finally {
    saving = false
  }
}