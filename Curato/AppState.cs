using Curato.ViewModels;

namespace Curato
{
    public static class AppState
    {
        public static InputViewModel SharedInputViewModel { get; } = new InputViewModel();
    }
}
