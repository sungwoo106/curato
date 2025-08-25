using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace Curato;

/// <summary>
/// Main application window
/// </summary>
public partial class MainWindow : Window
{
    /// <summary>
    /// Initializes the main window
    /// </summary>
    public MainWindow()
    {
        InitializeComponent();
        // Display the search page when the window loads
        MainFrame.Content = new Views.SearchPage();
    }

    /// <summary>
    /// Handles window loaded event to maximize window
    /// </summary>
    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        this.WindowState = WindowState.Normal;
        this.Left = SystemParameters.WorkArea.Left;
        this.Top = SystemParameters.WorkArea.Top;
        this.Width = SystemParameters.WorkArea.Width;
        this.Height = SystemParameters.WorkArea.Height;
    }

    /// <summary>
    /// Handles mouse drag to move window
    /// </summary>
    private void DragWindow(object sender, MouseButtonEventArgs e)
    {
        if (e.LeftButton == MouseButtonState.Pressed)
            this.DragMove();
    }
}