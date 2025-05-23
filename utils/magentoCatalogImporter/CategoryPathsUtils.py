import re
import logging
from lib.helper.CatalogImporterConfigHelper import config

class CategoryPathUtils:
    """
    Utility to handle category path normalization and validation
    """

    @staticmethod
    def normalizeCategoryPath(path):
        """
        Normalize a category path
        
        Args:
            path (str): Raw category path
            
        Returns:
            str: Normalized path
        """
        if not path or str(path).strip() == '':
            return None
            
        # Clean the path
        clean_path = str(path).strip()
        
        # Replace multiple slashes with single slash
        clean_path = re.sub(r'/+', '/', clean_path)
        
        # Remove leading and trailing slashes
        clean_path = clean_path.strip('/')
        
        if not clean_path:
            return None
            
        return clean_path

    @staticmethod
    def sortPathsByDepth(paths):
        """
        Sort paths by depth (shallower first)
        to ensure parent categories are created before children
        
        Args:
            paths (iterable): Collection of paths
            
        Returns:
            list: List of paths sorted by depth
        """
        return sorted(list(paths), key=lambda x: len(x.split('/')))

    @staticmethod
    def getConfiguredRootId():
        """
        Get root category ID from configuration
        
        Returns:
            int: Root category ID
        """
        # Try Bricozone first, then Zangoo as fallback
        root_id = config('CATEGORY_ROOT_ID_BRICOZONE', default=None, cast=int)
        
        if root_id is None:
            root_id = config('CATEGORY_ROOT_ID_ZANGOO', default=2, cast=int)
            logging.info(f"Using Zangoo root category: {root_id}")
        else:
            logging.info(f"Using Bricozone root category: {root_id}")
        
        return root_id

    @staticmethod
    def validatePaths(paths):
        """
        Validate a collection of paths, removing invalid ones
        
        Args:
            paths (iterable): Collection of paths to validate
            
        Returns:
            list: List of valid paths
        """
        valid_paths = []
        
        for path in paths:
            if not path or not isinstance(path, str):
                continue
                
            # Check that it's not just spaces
            if not path.strip():
                continue
                
            # Check that it doesn't contain only slashes
            if re.match(r'^/+$', path.strip()):
                continue
                
            # Normalize and validate
            normalized = CategoryPathUtils.normalizeCategoryPath(path)
            if normalized:
                valid_paths.append(normalized)
        
        return valid_paths

    @staticmethod
    def getPathDepth(path):
        """
        Get the depth level of a category path
        
        Args:
            path (str): Category path
            
        Returns:
            int: Depth level (number of segments)
        """
        if not path:
            return 0
        
        normalized = CategoryPathUtils.normalizeCategoryPath(path)
        if not normalized:
            return 0
            
        return len(normalized.split('/'))

    @staticmethod
    def getParentPath(path):
        """
        Get the parent path of a category path
        
        Args:
            path (str): Category path
            
        Returns:
            str|None: Parent path or None if root level
        """
        normalized = CategoryPathUtils.normalizeCategoryPath(path)
        if not normalized:
            return None
            
        segments = normalized.split('/')
        if len(segments) <= 1:
            return None  # Root level, no parent
            
        return '/'.join(segments[:-1])

    @staticmethod
    def getCategoryName(path):
        """
        Get the category name (last segment) from a path
        
        Args:
            path (str): Category path
            
        Returns:
            str|None: Category name or None if invalid
        """
        normalized = CategoryPathUtils.normalizeCategoryPath(path)
        if not normalized:
            return None
            
        segments = normalized.split('/')
        return segments[-1] if segments else None