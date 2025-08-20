using Curato.ViewModels;
using Curato.Models;

namespace Curato
{
    public static class AppState
    {
        public static InputViewModel SharedInputViewModel { get; } = new InputViewModel();
        public static TripPlan SharedTripPlan { get; set; } = new();

    }
}
