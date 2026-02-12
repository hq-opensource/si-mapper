import React from 'react';
import { FileText, Image as ImageIcon, Loader2, Search, Trash2, Upload, RefreshCw, Folder, FileSpreadsheet, File, Play, Pencil, PencilOff, ArrowLeft } from 'lucide-react';

// Local definition mirroring the CopilotChatIcons interface from @copilotkit/react-ui/dist/components/chat/ChatContext
interface LocalCopilotChatIcons {
    openIcon?: React.ReactNode;
    closeIcon?: React.ReactNode;
    headerCloseIcon?: React.ReactNode;
    sendIcon?: React.ReactNode;
    activityIcon?: React.ReactNode;
    spinnerIcon?: React.ReactNode;
    stopIcon?: React.ReactNode;
    regenerateIcon?: React.ReactNode;
    pushToTalkIcon?: React.ReactNode;
    copyIcon?: React.ReactNode;
    thumbsUpIcon?: React.ReactNode;
    thumbsDownIcon?: React.ReactNode;
    uploadIcon?: React.ReactNode;
}

/**
 * Defines the interface for all application-wide icons, extending LocalCopilotChatIcons.
 * This serves as the single source of truth for icon customization.
 */
export interface AppIcons extends LocalCopilotChatIcons {
    // FilesWindow specific icons
    fileTextIcon: React.ReactNode;
    imageFileIcon: React.ReactNode;
    uploadFileIcon: React.ReactNode;
    refreshIcon: React.ReactNode;
    trashIcon: React.ReactNode;
    searchIcon: React.ReactNode;
    loaderIcon: React.ReactNode;
    folderIcon: React.ReactNode;
    fileSpreadsheetIcon: React.ReactNode;
    genericFileIcon: React.ReactNode;
    playIcon: React.ReactNode;
    editIcon: React.ReactNode;
    viewIcon: React.ReactNode;
    backIcon: React.ReactNode;
}

/**
 * Default implementation for all application icons.
 * These will be used if no custom icons are provided via the AppIconsContextProvider.
 */
export const defaultAppIcons: AppIcons = {
    // CopilotChat default icons (placeholders, as we don't have access to their actual defaults)
    openIcon: null, // Placeholder
    closeIcon: null, // Placeholder
    headerCloseIcon: null, // Placeholder
    sendIcon: null, // Placeholder
    activityIcon: null, // Placeholder
    spinnerIcon: null, // Placeholder
    stopIcon: null, // Placeholder
    regenerateIcon: null, // Placeholder
    pushToTalkIcon: null, // Placeholder
    copyIcon: null, // Placeholder
    thumbsUpIcon: null, // Placeholder
    thumbsDownIcon: null, // Placeholder
    uploadIcon: null, // Placeholder for CopilotChat's upload icon

    // FilesWindow specific default icons
    fileTextIcon: <FileText />,
    imageFileIcon: <ImageIcon />,
    uploadFileIcon: <Upload />,
    refreshIcon: <RefreshCw />,
    trashIcon: <Trash2 />,
    searchIcon: <Search />,
    loaderIcon: <Loader2 />,
    folderIcon: <Folder />,
    fileSpreadsheetIcon: <FileSpreadsheet />,
    genericFileIcon: <File />,
    playIcon: <Play />,
    editIcon: <Pencil />,
    viewIcon: <PencilOff />,
    backIcon: <ArrowLeft />,
};