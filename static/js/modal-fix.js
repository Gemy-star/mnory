/**
 * modal-fix.js
 * Defensive monkey-patch for Bootstrap Modal to prevent runtime errors
 * 
 * This script patches the Bootstrap Modal._initializeBackDrop method to handle
 * cases where this._config is undefined, preventing TypeError exceptions.
 */

(function() {
    'use strict';
    
    // Wait for Bootstrap to be loaded
    if (typeof bootstrap === 'undefined' || typeof bootstrap.Modal === 'undefined') {
        console.warn('Bootstrap Modal not found. Skipping modal fix.');
        return;
    }
    
    // Guard: Only patch if _initializeBackDrop exists
    if (typeof bootstrap.Modal.prototype._initializeBackDrop !== 'function') {
        return;
    }
    
    // Store the original method
    const originalInitializeBackDrop = bootstrap.Modal.prototype._initializeBackDrop;
    
    // Monkey-patch with defensive wrapper
    bootstrap.Modal.prototype._initializeBackDrop = function() {
        try {
            // Guard: Check if this and this._config exist
            if (!this || !this._config) {
                console.warn('Modal._initializeBackDrop called with invalid context');
                return null;
            }
            
            // Call original method with proper context
            return originalInitializeBackDrop.apply(this, arguments);
        } catch (error) {
            console.error('Error in Modal._initializeBackDrop:', error);
            // Return early to prevent cascade failures
            return null;
        }
    };
    
    console.log('Bootstrap Modal defensive patch applied');
})();
