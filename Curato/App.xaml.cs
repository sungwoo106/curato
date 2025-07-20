using System.Configuration;
using System.Data;
using System.Windows;

namespace Curato;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
        protected override void OnStartup(StartupEventArgs e)
    {
        var window = new MainWindow();
        window.DataContext = new MainViewModel();
        window.Show();
    }
}

