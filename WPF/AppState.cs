using Curato.ViewModels;
using Curato.Models;

namespace Curato
{
    /// <summary>
    /// Global application state shared across views
    /// </summary>
    public static class AppState
    {
        /// <summary>
        /// Shared input view model for user preferences
        /// </summary>
        public static InputViewModel SharedInputViewModel { get; } = new InputViewModel();
        
        /// <summary>
        /// Shared trip plan containing generated itinerary data
        /// </summary>
        public static TripPlan SharedTripPlan { get; set; } = new();
    }
}
