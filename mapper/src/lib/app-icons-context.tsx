"use client";
import React, { createContext, useContext, ReactNode } from 'react';
import { AppIcons, defaultAppIcons } from './app-icons';

/**
 * Defines the shape of the AppIconsContext.
 */
interface AppIconsContextType {
    icons: AppIcons;
}

/**
 * Creates the AppIconsContext.
 */
const AppIconsContext = createContext<AppIconsContextType | undefined>(undefined);

/**
 * Props for the AppIconsContextProvider component.
 */
interface AppIconsContextProviderProps {
    icons?: Partial<AppIcons>;
    children: ReactNode;
}

/**
 * Provides the AppIconsContext to its children.
 * It merges custom icons with default icons.
 */
export const AppIconsContextProvider: React.FC<AppIconsContextProviderProps> = ({
    icons: customIcons,
    children,
}) => {
    const mergedIcons: AppIcons = {
        ...defaultAppIcons,
        ...customIcons,
    };

    return (
        <AppIconsContext.Provider value={{ icons: mergedIcons }}>
            {children}
        </AppIconsContext.Provider>
    );
};

/**
 * Custom hook to consume the AppIconsContext.
 * Throws an error if used outside of an AppIconsContextProvider.
 */
export const useAppIcons = (): AppIcons => {
    const context = useContext(AppIconsContext);
    if (context === undefined) {
        throw new Error('useAppIcons must be used within an AppIconsContextProvider');
    }
    return context.icons;
};