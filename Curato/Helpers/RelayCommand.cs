using System;
using System.Windows.Input;
using System.Windows;

// <summary>
// RelayCommand allows for command binding in WPF applications.
// It implements ICommand and provides a way to execute actions and determine if they can be executed.
// </summary>

namespace Curato.Helpers
{
    public class RelayCommand : ICommand
    {
        private readonly Action<object> _execute;
        private readonly Predicate<object>? _canExecute;

        public RelayCommand(Action<object> execute, Predicate<object>? canExecute = null)
        {
            _execute = execute;
            _canExecute = canExecute;
        }

        public bool CanExecute(object? parameter) => _canExecute?.Invoke(parameter!) ?? true;
        public void Execute(object? parameter) => _execute(parameter!);
        public event EventHandler? CanExecuteChanged
        {
            add => CommandManager.RequerySuggested += value;
            remove => CommandManager.RequerySuggested -= value;
        }
    }
}
