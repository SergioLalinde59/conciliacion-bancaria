
import { Checkbox } from '../atoms/Checkbox'

interface FilterTogglesProps {
    excluirTraslados?: boolean
    onExcluirTrasladosChange?: (checked: boolean) => void
    showExcluirTraslados?: boolean

    excluirPrestamos?: boolean
    onExcluirPrestamosChange?: (checked: boolean) => void
    showExcluirPrestamos?: boolean

    soloPendientes?: boolean
    onSoloPendientesChange?: (checked: boolean) => void
    showSoloPendientes?: boolean

    mostrarIngresos?: boolean
    onMostrarIngresosChange?: (checked: boolean) => void
    mostrarEgresos?: boolean
    onMostrarEgresosChange?: (checked: boolean) => void
    showIngresosEgresos?: boolean

    // Dynamic Filters
    configuracionExclusion?: Array<{ grupo_id: number; etiqueta: string }>;
    gruposExcluidos?: number[];
    onGruposExcluidosChange?: (ids: number[]) => void;
}

export const FilterToggles = ({
    excluirTraslados = false,
    onExcluirTrasladosChange,
    showExcluirTraslados = false,

    excluirPrestamos = false,
    onExcluirPrestamosChange,
    showExcluirPrestamos = false,

    soloPendientes = false,
    onSoloPendientesChange,
    showSoloPendientes = false,

    mostrarIngresos = true,
    onMostrarIngresosChange,
    mostrarEgresos = true,
    onMostrarEgresosChange,

    showIngresosEgresos = false,

    configuracionExclusion = [],
    gruposExcluidos = [],
    onGruposExcluidosChange
}: FilterTogglesProps) => {
    return (
        <div className="flex flex-wrap items-center gap-6">
            {/* Por Clasificar (Solo Pendientes) */}
            {showSoloPendientes && onSoloPendientesChange && (
                <Checkbox
                    label="Por Clasificar"
                    checked={!!soloPendientes}
                    onChange={(e) => onSoloPendientesChange(e.target.checked)}
                    className="text-amber-600 focus:ring-amber-500"
                />
            )}

            {/* Excluir Traslados */}
            {showExcluirTraslados && onExcluirTrasladosChange && (
                <Checkbox
                    label="Excluir Traslados"
                    checked={!!excluirTraslados}
                    onChange={(e) => onExcluirTrasladosChange(e.target.checked)}
                />
            )}

            {/* Dynamic Exclusion Filters (e.g. Tita) */}
            {configuracionExclusion
                // Exclude Traslados (ID 47) if the manual checkbox is shown
                .filter(config => !(showExcluirTraslados && config.grupo_id === 47))
                .sort((a, b) => b.etiqueta.localeCompare(a.etiqueta))
                .map(config => (
                    <Checkbox
                        key={config.grupo_id}
                        label={config.etiqueta}
                        checked={gruposExcluidos.includes(config.grupo_id)}
                        onChange={(e) => {
                            const isChecked = e.target.checked
                            const current = gruposExcluidos || []
                            if (isChecked) {
                                onGruposExcluidosChange?.([...current, config.grupo_id])
                            } else {
                                onGruposExcluidosChange?.(current.filter(id => id !== config.grupo_id))
                            }
                        }}
                    />
                ))}

            {/* Excluir Préstamos */}
            {showExcluirPrestamos && onExcluirPrestamosChange && (
                <Checkbox
                    label="Excluir Préstamos"
                    checked={!!excluirPrestamos}
                    onChange={(e) => onExcluirPrestamosChange(e.target.checked)}
                />
            )}

            {/* Income/Expense Filters */}
            {showIngresosEgresos && onMostrarIngresosChange && onMostrarEgresosChange && (
                <>
                    <Checkbox
                        label="Ver Ingresos"
                        checked={!!mostrarIngresos}
                        onChange={(e) => onMostrarIngresosChange(e.target.checked)}
                        className="text-emerald-600"
                    />
                    <Checkbox
                        label="Ver Egresos"
                        checked={!!mostrarEgresos}
                        onChange={(e) => onMostrarEgresosChange(e.target.checked)}
                        className="text-rose-600"
                    />
                </>
            )}
        </div>
    )
}
