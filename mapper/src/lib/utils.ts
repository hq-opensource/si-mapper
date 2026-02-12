import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatAgentName(name: string): string {
    if (!name) return "";

    // 1. Replace underscores with spaces
    let formatted = name.replace(/_/g, ' ');

    // 2. Split PascalCase/camelCase (insert space before capital letters)
    // PipeTemperatureSensorsAgent -> Pipe Temperature Sensors Agent
    formatted = formatted.replace(/([a-z])([A-Z])/g, '$1 $2');

    // 3. Handle cases where multiple capital letters are together (e.g. "HVACAgent" -> "HVAC Agent")
    formatted = formatted.replace(/([A-Z])([A-Z][a-z])/g, '$1 $2');

    return formatted;
}
